from flask import Blueprint, flash, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from .models import Cart, CartItem, Product, User
from . import db

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
    cart_items = CartItem.query.filter_by(cart_id=user.cart.cart_id).all() if user.cart else []
    
    total_cost = sum(item.product.price * item.quantity for item in cart_items)
    
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

# In your views or controller, when the user completes a purchase, create a new cart
@views.route('/checkout', methods=['POST'])
@login_required
def checkout():
    # Retrieve products from the user's cart
    user = current_user
    products_in_cart = user.cart

    # Calculate the total cost
    total_cost = db.session.query(func.sum(Product.price)).filter(Product.id.in_([product.id for product in products_in_cart])).scalar()

    if request.method == 'POST':
        # Handle payment processing here (e.g., with a payment gateway)

        # Create a new cart for the user
        create_new_cart(user)

        flash('Payment successful! Your order has been placed.', 'success')
        return redirect(url_for('views.catalog'))

    return render_template('checkout.html', products_in_cart=products_in_cart, user=current_user, total_cost=total_cost)

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

@views.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    product = Product.query.get(product_id)
    current_user.cart.remove(product)
    db.session.commit()
    return redirect(url_for('views.cart'))