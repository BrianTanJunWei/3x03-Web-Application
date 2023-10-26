import io
from datetime import datetime
from flask import Blueprint, flash, make_response, render_template, request, redirect, url_for, send_file
from flask_login import login_required, current_user
from sqlalchemy import func
from .models import Product, User, Cart, CartItem, Order, OrderItem
from . import db
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import joinedload

views = Blueprint('views', __name__)

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

@views.route('/cart')
@login_required
def cart():
    user = current_user
    cart = Cart.get_active_cart(user.id)  # Use the get_active_cart method from your models

    if cart:
        cart_items = cart.cart_items
        total_cost = sum(item.product.price * item.quantity for item in cart_items)
    else:
        cart_items = []
        total_cost = 0.0

    return render_template("cart.html", user=current_user, products_in_cart=cart_items, total_cost=total_cost)

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

@views.route('/account')
@login_required # prevents ppl from going to homepage without logging in
def account():
    account_status = get_user_role(current_user.id)
    return render_template("account.html", user=current_user, account_status=account_status)

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
        pdf_data = generate_order_pdf(current_user, cart_items, total_cost)

        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=order_summary.pdf'

        return response
    
    return render_template('checkout.html', user=current_user, products_in_cart=cart_items, total_cost=total_cost)

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

def generate_order_pdf(user, cart_items, total_cost):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Customize the PDF layout and content
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Order Summary")
    c.drawString(100, 730, f"User: {user.first_name} {user.last_name}")

    # Iterate through cart items
    y = 710  # Starting y-coordinate
    for cart_item in cart_items:
        product = cart_item.product
        c.drawString(100, y, f"Product: {product.name}")
        c.drawString(250, y, f"Quantity: {cart_item.quantity}")
        c.drawString(350, y, f"Price: ${product.price:.2f}")
        c.drawString(450, y, f"Subtotal: ${cart_item.quantity * product.price:.2f}")
        y -= 20  

    c.drawString(100, y, f"Total Cost: ${total_cost:.2f}")

    c.showPage()
    c.save()

    pdf_data = buffer.getvalue()
    buffer.close()

    return pdf_data

# Define a method to create a new cart
def create_new_cart(user):
    new_cart = Cart(user=user)
    db.session.add(new_cart)
    db.session.commit()
    return new_cart

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


@views.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if product:
        user = current_user  # Get the current user
        cart = Cart.get_active_cart(user.id)  # Get the user's active cart

        if cart:
            # Create a new CartItem and associate it with the user and the product
            cart_item = CartItem(cart=cart, product=product, quantity=1)
        else:
            # If the user doesn't have an active cart, create a new one
            cart = create_new_cart(user)
            cart_item = CartItem(cart=cart, product=product, quantity=1)

        db.session.add(cart_item)
        db.session.commit()
        flash(f'Added {product.name} to your cart!', 'success')
    else:
        flash('Product not found.', 'error')
    
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
