from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Cart, User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # search db 
        user = User.query.filter_by(email=email).first()
        if user:
            # Verify the password using the stored salt and hashed password
            if bcrypt.check_password_hash(user.password, password):
                # Password is correct, log the user in
                login_user(user, remember=True)
                account_status = user.account_status
                # session['account_status'] = account_status
                flash('Logged in successfully!', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect email or password. Try again', category='error')
        else:
            flash('User not found. Check your email.', category='error')
    
    return render_template("login.html", user=current_user)    

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        address = request.form.get('address')
        contact_number = request.form.get('contactNumber')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        # check if user exist
        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email already exist', category='error')
        elif len(email) < 4:
            flash('Invalid email', category='error')
        elif len(first_name) < 2:
            flash('Invalid first name', category='error')
        elif password1 != password2:
            flash('Passwords does not match', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 character', category='error')
        else:
            hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')
            new_user = User(email=email, first_name=first_name, last_name=last_name,address=address, contact_no=contact_number, password=hashed_password)
            
            db.session.add(new_user)

            db.session.commit()
            
            login_user(new_user, remember=True)

            flash('Sign up completed!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)