from datetime import datetime
from flask import Blueprint, app, flash, make_response, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
import stripe
from .models import Cart, CartItem, Order, OrderItem, Product, User
from . import db
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

views = Blueprint('views', __name__)

@views.route('/')
@login_required # prevents ppl from going to homepage without logging in
def home():
    products = Product.query.all()
    account_status = get_user_role(current_user.id)
    return render_template("catalog.html", user=current_user, products=products, account_status=account_status)

def get_user_role(id):
    user = User.query.get(id)
    if user:
        return user.account_status
    else:
        return 'guest'
    
@views.route('/product/<int:product_id>')
def view_product(product_id):
    product = Product.query.get(product_id)
    return render_template('product.html', user=current_user, product=product)

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

@views.route('/inventory')
@login_required # prevents ppl from going to homepage without logging in
def inventory():
    return render_template("inventory.html", user=current_user)

@views.route('/order')
@login_required # prevents ppl from going to homepage without logging in
def order():
    return render_template("order.html", user=current_user)

@views.route('/account')
@login_required # prevents ppl from going to homepage without logging in
def account():
    return render_template("account.html", user=current_user)

@views.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    user = current_user
    cart = Cart.get_active_cart(user.id)  # Use the get_active_cart method from your models

    cart_items = cart.cart_items
    total_cost = sum(item.product.price * item.quantity for item in cart_items)
    # Simulate a payment (marking the order as paid)
    if request.method == 'POST':
        # Create a Payment Intent with Stripe
        stripe.api_key = app.config['TEST_STRIPE_SECRET_KEY']
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total_cost * 100),  # Total cost in cents
            currency='usd',
            description='Your Order Description',
            payment_method_types=['card'],
        )

        # Pass the client_secret to the template
        client_secret = payment_intent.client_secret

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

    # Create a new product
    new_product = Product(name=name, description=description, price=price)

    # Save the image
    new_product.save_image(image_file)
    
    # Add the new product to the database
    db.session.add(new_product)
    db.session.commit()

    # Redirect to the shop page or wherever you want
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