from . import db
from flask_login import UserMixin 
from sqlalchemy.sql import func
from PIL import Image
from werkzeug.utils import secure_filename
from flask import request, current_app
import os


class Login(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    account_status = db.Column(db.Boolean)
    account_type = db.Column(db.Integer)
    failedLoginCounter = db.Column(db.Integer, default=0)

class UserAccounts(db.Model):
    email_address = db.Column(db.String(150), primary_key=True)
    address = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    contact_no = db.Column(db.Integer)

class StaffAccounts(db.Model):
    email_address = db.Column(db.String(150),primary_key=True)
    name = db.Column(db.String(150))

class AdminAccounts(db.Model):
    email_address = db.Column(db.String(150),primary_key=True)
    name = db.Column(db.String(150))

class Logs(db.Model):
    log_id = db.Column(db.Integer, primary_key=True)
    log_level = db.Column(db.String(150))
    log_type = db.Column(db.String(150))
    entity = db.Column(db.String(150))
    log_desc = db.Column(db.String(150))
    log_time = db.Column(db.DateTime)
    account_type = db.Column(db.String(150))
    account_id = db.Column(db.String(150))
    affected_id = db.Column(db.String(150))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f"Product('{self.name}', '{self.price}')"