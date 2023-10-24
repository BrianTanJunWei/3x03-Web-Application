from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import *
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
        user = Login.query.filter_by(email_address=email).first()
        if user:
            # Verify the password using the stored salt and hashed password
            if bcrypt.check_password_hash(user.password, password):
                # Password is correct, log the user in
                login_user(user, remember=True)
                flash('Logged in successfully!', category='success')
                # TODO: insert check for user account type here
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
        contact = request.form.get('contact')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        # check if user exist
        user = Login.query.filter_by(email_address=email).first()

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
            new_user_login = Login(email_address=email, password=hashed_password,
                                   account_status= True, account_type=2)
            new_user_accounts = UserAccounts(email_address=email, address=address, first_name=first_name
                                             ,last_name=last_name, contact_no=contact)
            # new_user_accounts = AdminAccounts(email_address=email, name= first_name + " " + last_name)
            db.session.add(new_user_login)
            db.session.add(new_user_accounts)
            db.session.commit()
            
            login_user(new_user_login, remember=True) # allows user to stay logged in

            flash('Sign up completed!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)