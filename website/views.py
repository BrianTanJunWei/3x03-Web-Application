from flask import Blueprint, render_template, request, redirect, url_for, send_file, flash
from flask_login import login_required, current_user
from .models import Product, Login, Logs, StaffAccounts, UserAccounts
import xlsxwriter
from io import BytesIO
from . import db
from sqlalchemy import func

views = Blueprint('views', __name__)

@views.route('/')
@login_required # prevents ppl from going to homepage without logging in
def home():
    products = Product.query.all()
    account_status = (current_user.account_type)
    return render_template("catalog.html", user=current_user, products=products, account_status=account_status)


@views.route('/product/<int:product_id>')
def view_product(product_id):
    product = Product.query.get(product_id)
    return render_template('product.html', user=current_user, product=product)

@views.route('/cart')
@login_required # prevents ppl from going to homepage without logging in
def cart():
    products_in_cart = current_user.cart
    
    # Calculate the total cost
    total_cost = db.session.query(func.sum(Product.price)).filter(Product.id.in_([product.id for product in products_in_cart])).scalar()
    return render_template("cart.html", user=current_user, products_in_cart=products_in_cart, total_cost=total_cost)

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
    # Retrieve products from the user's cart
    user = current_user
    products_in_cart = user.cart

    # Calculate the total cost
    total_cost = db.session.query(func.sum(Product.price)).filter(Product.id.in_([product.id for product in products_in_cart])).scalar()

    if request.method == 'POST':
        # Handle payment processing here (e.g., with a payment gateway)

        # After successful payment, you may want to clear the user's cart
        user.cart.clear()
        db.session.commit()

        flash('Payment successful! Your order has been placed.', 'success')
        return redirect(url_for('views.catalog'))

    return render_template('checkout.html', products_in_cart=products_in_cart, user=current_user, total_cost=total_cost)

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
    return redirect(url_for('views.shop'))

@views.route('/logs')
@login_required
def logs():
    user_type = current_user.account_type
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        logs = Logs.query.all()
        return render_template("admin_logs.html", user=current_user, logs=logs)
    
@views.route('/logs/<logs_id>')
@login_required
def view_log(logs_id):
    user_type = current_user.account_type
    valid = 1
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        logs = Logs.query.get(logs_id)
        if (logs is None):
            valid = 0
        return render_template("admin_log_details.html", user=current_user, logs=logs, valid=valid)

@views.route('/staffaccounts')
@login_required
def staffaccounts():
    user_type = current_user.account_type
    valid = 1
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        staff = StaffAccounts.query.all()
        users = Login.query.all()
        if (staff is None or users is None):
            valid = 0
        return render_template("admin_accounts.html", user=current_user, users=users, staff=staff, valid=valid)
    
@views.route('/staffaccounts/<staff_id>')
@login_required
def view_staff(staff_id):
    user_type = current_user.account_type
    valid = 1
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        staff = StaffAccounts.query.get(staff_id)
        staffinfo = Login.query.filter_by(email_address=staff_id).first()
        if (staff is None):
            valid = 0
        if (staffinfo is None):
            valid = 0
        return render_template("admin_staff_details.html", user=current_user, staff=staff, staffinfo=staffinfo, valid=valid)

@views.route('/staffdisable/<staff_id>')
@login_required
def disable_staff(staff_id):
    user_type = current_user.account_type
    valid = 1
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        staff = StaffAccounts.query.get(staff_id)
        staffinfo = Login.query.filter_by(email_address=staff_id).first()
        if (staff is None or staffinfo is None):
            valid = 0
            return redirect(url_for('views.home'))
        else:
            if(staffinfo.account_status == True):
                staffinfo.account_status = False
            else:
                staffinfo.account_status = True
            db.session.commit()
            return render_template("admin_staff_details.html", user=current_user, staff=staff, staffinfo=staffinfo, valid=valid)


           

@views.route('/download_logs_api')
@login_required
def downloadLogs():
    user_type = current_user.account_type
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        apiResponse = createApiResponse()
        return apiResponse
    
def createApiResponse():
    bufferFile = writeBufferExcelFile()
    mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return send_file(bufferFile, mimetype=mimetype)

def writeBufferExcelFile():
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer)
    worksheet = workbook.add_worksheet()
    logs = Logs.query.all()

    worksheet.write(0,0,"Log ID")
    worksheet.write(0,1,"Log Level")
    worksheet.write(0,2,"Log Type")
    worksheet.write(0,3,"Entity")
    worksheet.write(0,4,"Log Description")
    worksheet.write(0,5,"Log Time")
    worksheet.write(0,6,"Account Type")
    worksheet.write(0,7, "Account ID")
    worksheet.write(0,8,"Affected ID")

    vert = 1
    hor = 0
    for item in logs:
        worksheet.write(vert, hor, item.log_id)
        hor +=1
        worksheet.write(vert,hor, item.log_level)
        hor +=1
        worksheet.write(vert,hor, item.log_type)
        hor +=1
        worksheet.write(vert,hor, item.entity)
        hor +=1
        worksheet.write(vert,hor, item.log_desc)
        hor +=1
        worksheet.write(vert,hor, item.log_time)
        hor +=1
        worksheet.write(vert,hor, item.account_type)
        hor +=1
        worksheet.write(vert,hor, item.account_id)
        hor +=1
        worksheet.write(vert,hor, item.affected_id)
        vert+=1
        hor = 0
    
    workbook.close()
    buffer.seek(0)
    return buffer

@views.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if product:
        current_user.cart.append(product)
        db.session.commit()
        flash(f'Added {product.name} to your cart!', 'success')
    else:
        flash('Product not found.', 'error')
    
    return redirect(url_for('views.home'))

@views.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    product = Product.query.get(product_id)
    current_user.cart.remove(product)
    db.session.commit()
    return redirect(url_for('views.cart'))
