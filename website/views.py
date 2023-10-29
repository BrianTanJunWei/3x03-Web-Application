import io
from datetime import datetime
from flask import Blueprint, flash, make_response, make_response, render_template, request, redirect, url_for, send_file
from flask_login import login_required, current_user
from sqlalchemy import func
from .models import Cart, CartItem, Order, OrderItem, PasswordResetToken, Product, User, Cart, CartItem, Order, OrderItem
from . import SENDER_EMAIL, SENDINBLUE_API_KEY, db
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy.orm import joinedload
import requests
from flask_bcrypt import Bcrypt

views = Blueprint('views', __name__)
bcrypt = Bcrypt()

@views.route('/')
@login_required # prevents ppl from going to homepage without logging in
def home():
    products = Product.query.all()
    account_status = get_user_role(current_user.id)
    if account_status == 'staff':
        return render_template("staff_catalog.html", user=current_user, account_status=account_status, products=products)
    else:
        return render_template("customer_catalog.html", user=current_user, account_status=account_status, products=products)


def get_user_role(id):
    user = User.query.get(id)
    if user:
        return user.account_status
    else:
        return 'guest'
    
@views.route('/product/<int:product_id>')
def view_product(product_id):
    product = Product.query.get(product_id)
    account_status = get_user_role(current_user.id)
    return render_template('product.html', user=current_user, product=product, account_status=account_status)

@views.route('/inventory')
@login_required # prevents ppl from going to homepage without logging in
def inventory():
    return render_template("inventory.html", user=current_user)

@views.route('/order')
@login_required # prevents ppl from going to homepage without logging in
def order():
    account_status = get_user_role(current_user.id)
    if account_status == 'staff':
        # Staff members view all orders
        orders = Order.query.all()
        return render_template("all_orders.html", user=current_user, orders=orders, account_status=account_status)
    else:
        orders = Order.query.filter_by(customer=current_user.id).all()
        print(orders)  # Add this line for debugging
        return render_template("order.html", user=current_user, orders=orders)

@views.route('/order_details/<int:order_id>')
@login_required
def order_details(order_id):
    order = Order.query.get(order_id)

    if order:
        # Use joinedload to fetch related order_items and product data in a single query
        order = (
            Order.query
            .filter_by(order_id=order_id)
            .options(joinedload(Order.order_items).joinedload(OrderItem.product))
            .first()
        )

        return render_template('order_details.html', user=current_user, order=order, order_items=order.order_items)
    else:
        flash('Order not found', 'danger')
        return redirect(url_for('views.order_history'))

# staff
@views.route('/all_orders')
@login_required  # Use @login_required to ensure only staff members can access this route
def all_orders():
    account_status = get_user_role(current_user.id)
    # Add code to fetch all orders from all customers
    orders = Order.query.all()
    return render_template('all_orders.html', orders=orders, account_status=account_status)

@views.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    account_status = get_user_role(current_user.id)
    # Get the new status from the form
    new_status = request.form.get('new_status')
    
    # Find the order by ID
    order = Order.query.get(order_id)

    if order:
        # Update the order status
        order.order_status = new_status
        db.session.commit()
        flash(f'Order status updated to {new_status} for order ID {order_id}.', 'success')
    else:
        flash(f'Order with ID {order_id} not found.', 'danger')

    # Redirect back to the 'all_orders' page
    orders = Order.query.all()  # Fetch all orders again
    return render_template('all_orders.html', orders=orders, user=current_user, account_status=account_status)

@views.route('/generate_pdf', methods=['GET'])
def generate_pdf_content():
    filter_value = request.args.get('filter_value')
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Retrieve order
    if filter_value == "All" or filter_value == "":
        orders = Order.query.all()
        filter_value = "All"
    else:
        orders = Order.query.filter_by(order_status=filter_value).all()
    
    p.drawString(100, 750, f'Filtered Orders for Status: {filter_value}')
    y_position = 700  # Initial y-position
    for order in orders:
        y_position -= 20  # Move down for each order
        p.drawString(100, y_position, f'Order ID: {order.order_id}')
        
        # Retrieve order items for the current order
        order_items = OrderItem.query.filter_by(order=order).all()
        for order_item in order_items:
            y_position -= 20
            p.drawString(100, y_position, f'Product Name: {order_item.product.name}')
            y_position -= 20
            p.drawString(100, y_position, f'Quantity: {order_item.quantity}')

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='generated_pdf.pdf', mimetype='application/pdf')

@views.route('/add_product', methods=['POST'])
def add_product():
    # Get data from the request
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    image_file = request.files['image']
    is_hidden = bool(request.form.get('is_hidden'))

    # Create a new product
    new_product = Product(name=name, description=description, price=price, is_hidden=is_hidden)

    # Save the image
    new_product.save_image(image_file)
    
    # Add the new product to the database
    db.session.add(new_product)
    db.session.commit()

    # Redirect to the shop page or wherever you want
    return redirect(url_for('views.home'))

@views.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    # Fetch the product to be edited
    account_status = get_user_role(current_user.id)
    if account_status == "staff":
        product = Product.query.get(product_id)

        if request.method == 'POST':
            # Get the updated data from the form
            new_name = request.form.get('name')
            new_description = request.form.get('description')
            new_price = request.form.get('price')
            new_is_hidden = bool(request.form.get('is_hidden'))        

            # Update the product's data
            product.name = new_name
            product.description = new_description
            product.price = new_price
            product.is_hidden = new_is_hidden

            # Commit the changes to the database
            db.session.commit()

            # Redirect to the product's details page or wherever you want
            return redirect(url_for('views.home', product_id=product.id))
    else:
        flash("You do not have the permission to modify product info!", category="error")

# Route to account page
@views.route('/account', methods=['GET', 'POST'])
@login_required # prevents ppl from going to homepage without logging in
def account():
    user = current_user
    account_status = get_user_role(current_user.id)
    
    # Handle form submission if you want to allow users to update their information
    if request.method == 'POST':
        if request.form['submit_button'] == 'edit':
            # Handle form submission for the "Edit Information" button
            user.first_name = request.form.get('first_name')
            user.last_name = request.form.get('last_name')
            user.address = request.form.get('address')
            user.contact_no = request.form.get('contact_no')
            
            # Commit changes to the database
            db.session.commit()

    return render_template("account.html", user=user, account_status=account_status)

@views.route('/cart')
@login_required
def cart():
    user = current_user
    account_status = get_user_role(current_user.id)
    cart = Cart.get_active_cart(user.id)  # Use the get_active_cart method from your models

    if cart:
        cart_items = cart.cart_items

        # Remove hidden items from the cart
        for cart_item in cart_items:
            product = cart_item.product
            if product.is_hidden:
                db.session.delete(cart_item)
                db.session.commit()
        
        total_cost = sum(item.product.price * item.quantity for item in cart_items)
    
    else:
        cart_items = []
        total_cost = 0.0

    return render_template("cart.html", user=current_user, products_in_cart=cart_items, total_cost=total_cost, account_status=account_status)

# Define a method to create a new cart
def create_new_cart(user):
    new_cart = Cart(user=user)
    db.session.add(new_cart)
    db.session.commit()
    return new_cart

@views.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    user = current_user
    cart = Cart.get_active_cart(user.id)  # Use the get_active_cart method from your models

    cart_items = cart.cart_items
    total_cost = sum(item.product.price * item.quantity for item in cart_items)
    # Simulate a payment (marking the order as paid)
    if request.method == 'POST':
        mark_order_as_paid(current_user, total_cost)
        
        return render_template("confirmation.html", user=current_user, products_in_cart=cart_items, total_cost=total_cost)
    
    return render_template('checkout.html', user=current_user, products_in_cart=cart_items, total_cost=total_cost)

@views.route('/confirmation')
def confirmation():
    user = current_user
    cart = Cart.get_active_cart(user.id)  # Use the get_active_cart method from your models

    cart_items = cart.cart_items
    total_cost = sum(item.product.price * item.quantity for item in cart_items)

    pdf_data = generate_order_pdf(current_user, cart_items, total_cost)

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=order_summary.pdf'
    
    return render_template("confirmation.html", user=current_user, products_in_cart=cart_items, total_cost=total_cost)
    
def mark_order_as_paid(user, total_cost):
    
    # Create a new order for the user
    new_order = Order(customer=user.id, order_status='paid', placed_date=datetime.now())

    cart = Cart.get_active_cart(user.id)
    # Retrieve the products from the user's current cart
    cart_items = cart.cart_items

    for cart_item in cart_items:
        # Create an order item for each product in the cart
        order_item = OrderItem(order=new_order, product=cart_item.product, quantity=cart_item.quantity)
        db.session.add(order_item)

    # Mark the order as shipped (or do any other relevant processing)
    new_order.shipped_date = datetime.now()

    # Commit changes to the database
    db.session.add(new_order)
    db.session.commit()

    # Create a new cart for the user
    new_cart = Cart(customer=user.id)
    db.session.add(new_cart)
    
    # Commit changes to the database
    db.session.commit()    

@views.route('/view_pdf')
def view_pdf():
    user = current_user
    cart = Cart.get_active_cart(user.id)

    if cart:
        cart_items = cart.cart_items
        total_cost = sum(item.product.price * item.quantity for item in cart_items)
    else:
        cart_items = []
        total_cost = 0.0

    pdf_data = generate_order_pdf(user, cart_items, total_cost)

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=order_summary.pdf'

    return response

def generate_order_pdf(user, cart_items, total_cost):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Create a list to hold PDF elements
    elements = []

    # Styles for the PDF
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("Order Summary", styles['Title'])
    elements.append(title)

    # Date
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_text = f"Order Date: {current_date}"
    elements.append(Paragraph(date_text, styles['Normal']))
    
    # User information
    user_info = f"User: {user.first_name} {user.last_name}"
    if user.address:
        user_info += f"<br />Address: {user.address}"
    elements.append(Paragraph(user_info, styles['Normal']))
    elements.append(Spacer(1, 12))

    # Table to display order details
    order_data = [["Product", "Quantity", "Price", "Subtotal"]]
    for cart_item in cart_items:
        product = cart_item.product
        order_data.append([product.name, cart_item.quantity, f"${product.price:.2f}", f"${cart_item.quantity * product.price:.2f}"])
    order_table = Table(order_data)
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(order_table)
    elements.append(Spacer(1, 12))

    # Total cost
    total_cost_text = f"Total Cost: ${total_cost:.2f}"
    elements.append(Paragraph(total_cost_text, styles['Normal']))

    doc.build(elements)

    pdf_data = buffer.getvalue()
    buffer.close()

    return pdf_data

@views.route('/clear_cart')
@login_required
def clear_cart():
    user = current_user
    # Get the user's active cart
    cart = Cart.get_active_cart(user.id)

    if cart:
        # Delete all cart items associated with the cart
        CartItem.query.filter_by(cart_id=cart.cart_id).delete()
        # Commit the changes to remove cart items
        db.session.commit()

    # Redirect the user back to the catalog
    return redirect(url_for('views.home'))


@views.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user = current_user
    product = Product.query.get(product_id)
    
    # Check if the user has an active cart, and create one if it doesn't exist
    cart = Cart.get_active_cart(user.id)
    if cart is None:
        cart = Cart(customer=user.id)
        db.session.add(cart)
        db.session.commit()
        
    # Add the product to the user's cart
    cart_item = CartItem(cart_id=cart.cart_id, product_id=product.id, quantity=1)
    
    db.session.add(cart_item)
    db.session.commit()
    
    flash(f'{product.name} added to your cart.', 'success')
    
    return redirect(url_for('views.home'))

@views.route('/remove_from_cart/<int:product_id>', methods=['GET', 'POST'])
@login_required
def remove_from_cart(product_id):
    user = current_user
    cart = Cart.get_active_cart(user.id)  # Get the user's active cart

    if cart:
        product = Product.query.get(product_id)
        cart_item = CartItem.query.filter_by(cart_id=cart.cart_id, product_id=product_id).first()

        if cart_item:
            # Remove the cart item and commit the changes
            db.session.delete(cart_item)
            db.session.commit()

    return redirect(url_for('views.cart'))

@views.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Find the token in the database
    password_reset_token = PasswordResetToken.query.filter_by(token=token).first()

    if not password_reset_token:
        flash("Invalid or expired password reset token.", "danger")
        return redirect(url_for('auth.login'))  # Redirect to the login page or another appropriate page

    # Check if the token has expired
    token_age = datetime.now() - password_reset_token.timestamp
    if token_age.total_seconds() > 300:  # Adjust the expiration time as needed
        flash("Password reset token has expired. Please request a new one.", "danger")
        return redirect(url_for('auth.login'))  # Redirect to the login page or another appropriate page

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("New password and confirmation do not match.", "danger")
            return redirect(url_for('views.reset_password', token=token))

        # Hash the new password and update the user's password
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user = User.query.get(password_reset_token.user_id)
        user.password = hashed_password

        # Remove the password reset token after a successful password reset
        db.session.delete(password_reset_token)
        db.session.commit()

        flash("Password updated successfully.", "success")
        return redirect(url_for('auth.login'))

    return render_template("reset_password.html")

@views.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            # Create a password reset token and save it in the database
            token = PasswordResetToken(user_id=user.id)
            db.session.add(token)
            db.session.commit()

            # Send an email to the user with the password reset link
            send_password_reset_email(user, token.token)

            flash('An email with instructions to reset your password has been sent.', 'info')
            return redirect(url_for('auth.login'))

        flash('No user found with this email address.', 'danger')

    return render_template('request_password_reset.html')

def send_password_reset_email(user, token):
    # Create the email content
    email_content = f"""
    <p>Hello {user.first_name},</p>
    <p>You recently requested to reset your password. Click the link below to reset your password:</p>
    <p><a href="{request.host_url}reset_password/{token}">Reset Password</a></p>
    <p>If you didn't make this request, you can ignore this email.</p>
    <p>Thank you.</p>
    """

    # Send the email using the SendinBlue API
    headers = {
        'api-key': SENDINBLUE_API_KEY,
        'Content-Type': 'application/json',
    }
    data = {
        'to': [{'email': user.email}],
        'subject': 'Password Reset Request',
        'htmlContent': email_content,
        'sender': {'email': SENDER_EMAIL},
    }

    try:
        response = requests.post('https://api.sendinblue.com/v3/smtp/email', headers=headers, json=data)
        if response.status_code == 201:
            print("Password reset email sent successfully.")
        else:
            print(f"Error sending password reset email: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while sending the password reset email: {str(e)}")