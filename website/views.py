from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from .models import Product, Login
from . import db

views = Blueprint('views', __name__)

@views.route('/')
@login_required # prevents ppl from going to homepage without logging in
def home():
    return render_template("shop.html", user=current_user)

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
    return redirect(url_for('views.shop'))

@views.route('/logs')
@login_required
def logs():
    user_type = current_user.account_type
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        return render_template("admin_logs.html", user=current_user)

@views.route('/staffaccounts')
@login_required
def staffaccounts():
    user_type = current_user.account_type
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        return render_template("admin_accounts.html", user=current_user)