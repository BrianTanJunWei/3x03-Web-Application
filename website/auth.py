from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Login, UserAccounts, StaffAccounts, Logs
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import re

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()

email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
password_regex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$")

def validate_email(email):
    return email_regex.match(email)

def validate_password(password):
    return password_regex.match(password)


# Create an instance of the Flask app

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate email and password format
        if not validate_email(email):
            flash('Invalid email format.', category='error')
            return render_template("login.html", user=current_user)

        # search db
        user = Login.query.filter_by(email_address=email).first()

        if user:
            if user.account_status == False:
                log_entry = Logs(
                    log_level='WARNING',
                    log_type='Account Lockout',
                    entity='User',
                    log_desc='Account locked out due to multiple failed login attempts',
                    log_time=datetime.now(),
                    account_type=user.account_type,
                    account_id=user.id,
                    affected_id=user.email_address
                )
                db.session.add(log_entry)
                db.session.commit()

                flash('Account locked out, please contact the administrator', category="error")
            else:
                # Verify the password using the stored salt and hashed password
                if bcrypt.check_password_hash(user.password, password):
                    # Password is correct, log the user in
                    login_user(user, remember=True)

                    # Log successful login
                    log_entry = Logs(
                        log_level='INFO',
                        log_type='Login',
                        entity='User',
                        log_desc=f'User {user.email_address} logged in successfully.',
                        log_time=datetime.now(),
                        account_type=user.account_type,
                        account_id=user.id,
                        affected_id='null'
                    )
                    db.session.add(log_entry)
                    db.session.commit()

                    if user.account_type == 2:
                        # customer account
                        # flash('Logged in as a customer', category='success')
                        return redirect(url_for('views.home'))
                    elif user.account_type == 1:
                        # staff account
                        flash('Logged in as a staff member', category='success')
                        return redirect(url_for('views.home'))
                    elif user.account_type == 0:
                        # admin account
                        flash('Logged in as an admin', category='success')
                        return redirect(url_for('views.home'))
                    else:
                        flash('Unknown account type', category='error')
                else:
                    # Log unsuccessful login
                    log_entry = Logs(
                        log_level='ERROR',
                        log_type='Login',
                        entity='User',
                        log_desc=f'User login failed for email {email}.',
                        log_time=datetime.now(),
                        account_type='null',
                        account_id='null',
                        affected_id='null'
                    )
                    db.session.add(log_entry)
                    db.session.commit()

                    flash('Incorrect email or password. Try again', category='error')
        else:

            flash('User not found. Check your email.', category='error')


    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))


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
        elif not validate_password(password1):
            flash('Password must be at least 8 characters, including 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character.', category='error')
        else:
            hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')
            new_user_login = Login(email_address=email, password=hashed_password,
                                   account_status=True, account_type=2)
            new_user_accounts = UserAccounts(email_address=email, address=address, first_name=first_name
                                             , last_name=last_name, contact_no=contact)
            # new_user_accounts = AdminAccounts(email_address=email, name= first_name + " " + last_name)
            db.session.add(new_user_login)
            db.session.add(new_user_accounts)
            db.session.commit()

            login_user(new_user_login, remember=True)  # allows user to stay logged in

            
            # User Signup
            log_entry = Logs(
                log_level='INFO',
                log_type='Signup success',
                entity='User',
                log_desc='User signup successfully',
                log_time=datetime.now(),
                account_type='2',
                account_id=new_user_accounts.email_address,
                affected_id=new_user_accounts.first_name
            )
            db.session.add(log_entry)
            db.session.commit()

            flash('Sign up completed!', category='success')
            return redirect(url_for('auth.login'))

    return render_template("sign_up.html", user=current_user)


@auth.route('/adminstaffcreation', methods=['GET', 'POST'])
@login_required
def create_staff():
    account_status = (current_user.account_type)
    user_type = current_user.account_type
    if (user_type != 0):
        return redirect(url_for('views.home'))
    else:
        if request.method == 'POST':
            email = request.form.get('email')
            name = request.form.get('name')
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')
            # check if user exist
            user = Login.query.filter_by(email_address=email).first()

            if user:
                flash('Email already exist', category='error')
            elif not validate_email(email):
                flash('Invalid email address.', category='error')
            elif password1 != password2:
                flash('Passwords does not match', category='error')
            elif not validate_password(password1):
                flash('Password must be at least 8 characters, including 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character.', category='error')
            else:
                hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')
                new_user_login = Login(email_address=email, password=hashed_password,
                                       account_status=True, account_type=1)
                new_user_accounts = StaffAccounts(email_address=email, name=name)
                # new_user_accounts = AdminAccounts(email_address=email, name= first_name + " " + last_name)
                db.session.add(new_user_login)
                db.session.add(new_user_accounts)
                db.session.commit()

                log_entry = Logs(
                    log_level='INFO',
                    log_type='Signup success for staff',
                    entity='Admin',
                    log_desc='Staff creation successfully',
                    log_time=datetime.now(),
                    account_type=account_status,
                    account_id=current_user.email_address,
                    affected_id=new_user_accounts.email_address
                )
                db.session.add(log_entry)
                db.session.commit()
                flash('Staff Account Created!', category='success')
                return redirect(url_for('views.staffaccounts'))

        return render_template("admin_create_staff.html", user=current_user, account_status=account_status)
