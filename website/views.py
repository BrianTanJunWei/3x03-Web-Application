from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from .models import Product
from . import db

views = Blueprint('views', __name__)

@views.route('/')
@login_required # prevents ppl from going to homepage without logging in
def home():
    products = Product.query.all()
    return render_template("catalog.html", user=current_user, products=products)

@views.route('/product/<int:product_id>')
def view_product(product_id):
    product = Product.query.get(product_id)
    return render_template('product.html', product=product)

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

@views.route('/add_product', methods=['POST'])
def add_product():
    # Get data from the request
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    image_url = request.form.get('image_url')

    # Create a new product
    new_product = Product(name=name, description=description, price=price, image_url=image_url)

    # Add the new product to the database
    db.session.add(new_product)
    db.session.commit()

    # Redirect to the shop page or wherever you want
    return redirect(url_for('views.catalog'))
