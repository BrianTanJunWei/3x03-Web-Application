from sqlalchemy.orm import joinedload
import requests
from flask_bcrypt import Bcrypt

views = Blueprint('views', __name__)
bcrypt = Bcrypt()

@views.route('/')
def home():
    products = Product.query.all()

    if current_user.is_authenticated:
        account_status = (current_user.account_type)

        if account_status in (0,1):
            return render_template("staff_catalog.html", user=current_user, account_status=account_status, products=products)
        elif account_status == 2:
            return render_template("customer_catalog.html", user=current_user, account_status=account_status, products=products)
    else:
        return render_template("catalog.html", user=current_user, products=products)

@views.route('/product/<int:product_id>')
def view_product(product_id):
    product = Product.query.get(product_id)
	@@ -42,16 +48,17 @@ def view_product(product_id):
    else:
        return render_template('product.html', user=None, product=product, account_status=None)

@views.route('/order')
@login_required # prevents ppl from going to homepage without logging in
def order():
    account_status = (current_user.account_type)
    if account_status == 1:
        # Staff members view all orders
        customer_first_name = ""  # Define it here with an initial value
        total_cost = 0.0  # Define total_cost here with an initial value
        orders = Order.query.all()
        
        customer_first_names = []  # Create a list to store first names
        total_costs = []  # Create a list to store total costs

	@@ -60,13 +67,17 @@ def order():
            customer_details = UserAccounts.query.get(customer.email_address)
            customer_first_names.append(customer_details.first_name)
            total_costs.append(calculate_total_cost(order))
        return render_template("all_orders.html", user=current_user, orders=orders, customer_first_names=customer_first_names, account_status=account_status, total_costs=total_costs)
    else:
        orders = Order.query.filter_by(customer=current_user.id).all()
        total_cost = 0.0
        for order in orders:
            total_cost = calculate_total_cost(order)
        return render_template("order.html", user=current_user, orders=orders, account_status=account_status, total_cost=total_cost)

def calculate_total_cost(order):
    total_cost = 0.0
	@@ -76,6 +87,7 @@ def calculate_total_cost(order):
        total_cost += product.price * order_item.quantity
    return total_cost

@views.route('/order_details/<int:order_id>')
@login_required
def order_details(order_id):
	@@ -84,26 +96,29 @@ def order_details(order_id):

    if order:
        order_items = OrderItem.query.filter_by(order_id=order_id).all()
        
        order_items_with_products = []
        for order_item in order_items:
            product = Product.query.get(order_item.product_id)
            order_items_with_products.append((order_item, product))

        total_cost = calculate_total_cost(order)
        return render_template('order_details.html', user=current_user, order=order, order_items_with_products=order_items_with_products, order_items=order_items, total_cost=total_cost)
    else:
        flash('Order not found', 'danger')
        return redirect(url_for('views.order_history'))

@views.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    account_status = (current_user.account_type)
    if account_status == 1:
        # Get the new status from the form
        new_status = request.form.get('new_status')
    
        # Find the order by ID
        order = Order.query.get(order_id)

	@@ -115,9 +130,22 @@ def update_order_status(order_id):
        else:
            flash(f'Order with ID {order_id} not found.', 'danger')

        # Redirect back to the 'all_orders' page
        orders = Order.query.all()  # Fetch all orders again
        
        customer_first_names = []  # Create a list to store first names
        total_costs = []  # Create a list to store total costs

	@@ -126,7 +154,11 @@ def update_order_status(order_id):
            customer_details = UserAccounts.query.get(customer.email_address)
            customer_first_names.append(customer_details.first_name)
            total_costs.append(calculate_total_cost(order))
        return render_template("all_orders.html", user=current_user, orders=orders, customer_first_names=customer_first_names, account_status=account_status, total_costs=total_costs)
@views.route('/generate_pdf', methods=['GET'])
def generate_pdf_content():
    filter_value = request.args.get('filter_value')
	@@ -139,15 +171,15 @@ def generate_pdf_content():
        filter_value = "All"
    else:
        orders = Order.query.filter_by(order_status=filter_value).all()
    
    p.drawString(100, 750, f'Filtered Orders for Status: {filter_value}')
    y_position = 700  # Initial y-position
    for order in orders:
        y_position -= 20  # Move down for each order
        p.drawString(100, y_position, f'Order ID: {order.order_id}')
        
        # Retrieve order items for the current order
        
        order_items = OrderItem.query.filter_by(order_id=order.order_id).all()
        for order_item in order_items:
            product = Product.query.get(order_item.product_id)
	@@ -162,6 +194,7 @@ def generate_pdf_content():

    return send_file(buffer, as_attachment=True, download_name='generated_pdf.pdf', mimetype='application/pdf')

@views.route('/add_product', methods=['POST'])
def add_product():
    account_status = (current_user.account_type)
	@@ -178,16 +211,31 @@ def add_product():

        # Save the image
        new_product.save_image(image_file)
    
        # Add the new product to the database
        db.session.add(new_product)
        db.session.commit()
        flash(f'{new_product.name} with the price of ${new_product.price} have been added to the catalog.', 'success')

        # Redirect to the shop page or wherever you want
        return redirect(url_for('views.home'))
    else:
        flash("You do not have the permission to add product!", category="error")

# @views.route('/remove_product/<int:product_id>', methods=['POST'])
# def remove_product(product_id):
	@@ -206,7 +254,7 @@ def add_product():
#                 # Remove related cart items
#                 for cart_item in cart_items:
#                     db.session.delete(cart_item)
            
#             # Perform the removal
#             db.session.delete(product_to_remove)
#             db.session.commit()
	@@ -229,15 +277,27 @@ def edit_product(product_id):
    if account_status == 1:
        product = Product.query.get(product_id)

        if request.method == 'POST':
            # Get the updated data from the form
            new_name = request.form.get('name')
            new_description = request.form.get('description')
            new_price = request.form.get('price')
            new_image_file = request.files['image']
            new_is_hidden = bool(request.form.get('is_hidden'))        


            # Update the product's data
            product.name = new_name
            product.description = new_description
	@@ -247,31 +307,31 @@ def edit_product(product_id):
            if new_image_file:
                # Save the new image and update the product's image path
                product.save_image(new_image_file)
                
            # Commit the changes to the database
            db.session.commit()
            flash(f'{product.name} have been successfully modified.', 'success')
            
            # Redirect to the product's details page or wherever you want
            return redirect(url_for('views.home', product_id=product.id))
    else:
        flash("You do not have the permission to modify product info!", category="error")

# Route to account page
@views.route('/account', methods=['GET', 'POST'])
@login_required # prevents ppl from going to homepage without logging in
def account():
    user = UserAccounts.query.filter_by(email_address=current_user.email_address).first()
    account_status = (current_user.account_type)
    # Handle form submission if you want to allow users to update their information
    if request.method == 'POST':

        # Handle form submission for the "Edit Information" button
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.address = request.form.get('address')
        user.contact_no = request.form.get('contact_no')
        
        # Commit changes to the database
        db.session.commit()

	@@ -283,9 +343,9 @@ def account():
def cart():
    user = current_user
    account_status = (current_user.account_type)
    
    # Use the get_active_cart method from your models
    cart = Cart.get_active_cart(user.id)  

    if cart:
        # Query the CartItem model to get cart items associated with the cart
	@@ -300,14 +360,16 @@ def cart():
            else:
                db.session.delete(cart_item)
                db.session.commit()
                
        total_cost = sum(product.price * cart_item.quantity for cart_item, _ in cart_items_with_products)
        
    else:   
        cart_items_with_products = []
        total_cost = 0.0

    return render_template("cart.html", user=current_user, cart_items_with_products=cart_items_with_products, total_cost=total_cost, account_status=account_status)

# Define a method to create a new cart
def create_new_cart(user):
	@@ -324,23 +386,26 @@ def checkout():
    cart = Cart.get_active_cart(user.id)  # Use the get_active_cart method from your models

    cart_items = CartItem.query.filter_by(cart_id=cart.cart_id).all()
    
    cart_items_with_products = []
    
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        if product and not product.is_hidden:
            cart_items_with_products.append((cart_item, product))
                
    total_cost = sum(product.price * cart_item.quantity for cart_item, _ in cart_items_with_products)

    # Simulate a payment (marking the order as paid)
    if request.method == 'POST':
        mark_order_as_paid(current_user, total_cost)

        return render_template("confirmation.html", user=current_user, cart_items_with_products=cart_items_with_products, total_cost=total_cost)

    return render_template('checkout.html', user=current_user, cart_items_with_products=cart_items_with_products, total_cost=total_cost)

@views.route('/confirmation')
def confirmation():
	@@ -355,9 +420,9 @@ def confirmation():
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=order_summary.pdf'
    
    return render_template("confirmation.html", user=current_user, products_in_cart=cart_items, total_cost=total_cost)
    

def mark_order_as_paid(user, total_cost):
    account_status = (current_user.account_type)
	@@ -368,22 +433,24 @@ def mark_order_as_paid(user, total_cost):
        # Commit changes to the database
        db.session.add(new_order)
        db.session.commit()
        
        cart = Cart.get_active_cart(user.id)
        # Retrieve the products from the user's current cart
        cart_items = CartItem.query.filter_by(cart_id=cart.cart_id).all()

        for cart_item in cart_items:
            # Create an order item for each product in the cart
            order_item = OrderItem(order_id=new_order.order_id, product_id=cart_item.product_id, quantity=cart_item.quantity)
            db.session.add(order_item)

        # Create a new cart for the user
        new_cart = Cart(customer=user.id)
        db.session.add(new_cart)
        
        # Commit changes to the database
        db.session.commit()    

@views.route('/view_pdf')
def view_pdf():
	@@ -392,7 +459,7 @@ def view_pdf():

    if cart:
        cart_items = CartItem.query.filter_by(cart_id=cart.cart_id).all()
        
        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)
        total_cost = sum(product.price * cart_item.quantity for cart_item in cart_items)
	@@ -401,15 +468,15 @@ def view_pdf():
        total_cost = 0.0

    pdf_data = generate_order_pdf(user, cart_items, total_cost)
    
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=order_summary.pdf'

    return response

def generate_order_pdf(user, cart_items, total_cost):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

	@@ -427,7 +494,7 @@ def generate_order_pdf(user, cart_items, total_cost):
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_text = f"Order Date: {current_date}"
    elements.append(Paragraph(date_text, styles['Normal']))
    
    # User information
    user_info = f"User: {user.first_name} {user.last_name}"
    if user.address:
	@@ -439,7 +506,8 @@ def generate_order_pdf(user, cart_items, total_cost):
    order_data = [["Product", "Quantity", "Price", "Subtotal"]]
    for cart_item in cart_items:
        product = product = Product.query.get(cart_item.product_id)
        order_data.append([product.name, cart_item.quantity, f"${product.price:.2f}", f"${cart_item.quantity * product.price:.2f}"])
    order_table = Table(order_data)
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
	@@ -464,6 +532,7 @@ def generate_order_pdf(user, cart_items, total_cost):

    return pdf_data

@views.route('/clear_cart')
@login_required
def clear_cart():
	@@ -486,24 +555,25 @@ def clear_cart():
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
	@@ -521,6 +591,7 @@ def remove_from_cart(product_id):

    return redirect(url_for('views.cart'))

@views.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    token_obj = PasswordResetToken.query.filter_by(token=token).first()
	@@ -533,27 +604,28 @@ def reset_password(token):
            # Update the user's password (assuming you have a user_id associated with the token)
            user_id = token_obj.user_id
            user = Login.query.filter_by(id=user_id).first()
            
            if user:
                # Update the user's password in the database
                user.password = bcrypt.generate_password_hash(new_password)  # You need to implement a password hashing function
                db.session.commit()
                
                # Delete the used token
                db.session.delete(token_obj)
                db.session.commit()
                
                flash('Your password has been reset. You can now log in with your new password.', 'success')
                return redirect(url_for('auth.login'))
        
        return render_template('reset_password.html')
    else:
        flash('This password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

@views.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():

    if request.method == 'POST':
        email = request.form.get('email')
        user = Login.query.filter_by(email_address=email).first()
	@@ -564,15 +636,29 @@ def request_password_reset():
            db.session.add(token)
            db.session.commit()

            # Send an email to the user with the password reset link
            send_password_reset_email(user_details, token.token)

            flash('An email with instructions to reset your password has been sent.', 'info')
            return redirect(url_for('auth.login'))

        flash('No user found with this email address.', 'danger')

    return render_template('request_password_reset.html')

def send_password_reset_email(user, token):
    # Create the email content
	@@ -606,35 +692,36 @@ def send_password_reset_email(user, token):
        print(f"An error occurred while sending the password reset email: {str(e)}")




# admin - useless
@views.route('/logs')
@login_required
def logs():
    account_status = (current_user.account_type)
    user = current_user
    user_type = current_user.account_type
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        logs = Logs.query.all()
        return render_template("admin_logs.html", user=current_user, logs=logs, account_status=account_status)

@views.route('/logs/<logs_id>')
@login_required
def view_log(logs_id):
    account_status = (current_user.account_type)
    user = current_user
    user_type = current_user.account_type
    valid = 1
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        logs = Logs.query.get(logs_id)
        if (logs is None):
            valid = 0
        return render_template("admin_log_details.html", user=current_user, logs=logs, valid=valid, account_status=account_status)

@views.route('/staffaccounts')
@login_required
	@@ -643,38 +730,42 @@ def staffaccounts():
    user = current_user
    user_type = current_user.account_type
    valid = 1
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        staff = StaffAccounts.query.all()
        users = Login.query.all()
        if (staff is None or users is None):
            valid = 0
        return render_template("admin_accounts.html", user=current_user, users=users, staff=staff, valid=valid, account_status=account_status)

@views.route('/staffaccounts/<staff_id>')
@login_required
def view_staff(staff_id):
    account_status = (current_user.account_type)
    user_type = current_user.account_type
    valid = 1
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        staff = Login.query.filter_by(id=staff_id).first()
        staffinfo= StaffAccounts.query.get(staff.email_address)
        if (staff is None):
            valid = 0
        if (staffinfo is None):
            valid = 0
        return render_template("admin_staff_details.html", user=current_user, staff=staff, staffinfo=staffinfo, valid=valid, account_status=account_status)

@views.route('/staffdisable/<staff_id>')
@login_required
def disable_staff(staff_id):
    user_type = current_user.account_type
    valid = 1
    if(user_type != 0):
        return redirect(url_for('views.home'))
    else:
        staff = Login.query.filter_by(id=staff_id).first()
	@@ -683,67 +774,71 @@ def disable_staff(staff_id):
            valid = 0
            return redirect(url_for('views.home'))
        else:
            if(staff.account_status == True):
                staff.account_status = False
            else:
                staff.account_status = True
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
