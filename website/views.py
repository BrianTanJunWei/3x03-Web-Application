from flask import Blueprint, render_template, request, redirect, url_for, send_file
from flask_login import login_required, current_user
from .models import Product, Login, Logs, StaffAccounts
import xlsxwriter
from io import BytesIO
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