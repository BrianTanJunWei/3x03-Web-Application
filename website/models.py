import base64
from sqlalchemy import LargeBinary
from . import db
from flask_login import UserMixin 
from sqlalchemy.sql import func
from PIL import Image
from io import BytesIO
from flask import request, current_app
from datetime import datetime, timedelta
import os
import secrets
import string
import pytz


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
    image = db.Column(db.String(255), nullable=True)
    is_hidden = db.Column(db.Boolean, default=True)
   
    
    def __repr__(self):
        return f"Product('{self.name}', '{self.price}')"
    
    def save_image(self, image_file):
        if image_file:
            img = Image.open(image_file)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            output = BytesIO()
            img.save(output, format='JPEG')
            image_data = output.getvalue()
            self.image = base64.b64encode(image_data).decode('utf-8')
            
class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
   
    
    @classmethod
    def get_active_cart(cls, user_id):
        return cls.query.filter_by(customer=user_id, is_active=True).first()
    
# CartItems Table
class CartItem(db.Model):
    cart_item_id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    
    
# Order Table
class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.String(20))
    placed_date = db.Column(db.DateTime)
    shipped_date = db.Column(db.DateTime)
    delivered_date = db.Column(db.DateTime)

    def calculate_total_cost(self):
        total_cost = 0.0
        for order_item in self.order_items:
            total_cost += order_item.product.price * order_item.quantity
        return total_cost

# OrderItems Table
class OrderItem(db.Model):
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    token = db.Column(db.String(100), nullable=False, unique=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, user_id):
        self.user_id = user_id
        self.token = generate_unique_token()
        self.timestamp = datetime.now(pytz.timezone('Asia/Singapore'))

    def is_expired(self):
        return datetime.utcnow() > self.timestamp + timedelta(minutes=5)

def generate_unique_token(token_length=50):
    characters = string.ascii_letters + string.digits
    while True:
        token = ''.join(secrets.choice(characters) for _ in range(token_length))
        if not PasswordResetToken.query.filter_by(token=token).first():
            return token