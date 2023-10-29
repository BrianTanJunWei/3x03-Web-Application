import base64
from sqlalchemy import LargeBinary
from . import db
from flask_login import UserMixin 
from sqlalchemy.sql import func
from PIL import Image
from io import BytesIO
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
    cart = db.relationship("Product", back_populates="users")
    carts = db.relationship("Cart", back_populates="customer")
    orders = db.relationship("Order", back_populates="customer")

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image = db.Column(db.String(255), nullable=True)
    users = db.relationship("User", back_populates="cart")
    cart_items = db.relationship("CartItem", back_populates="product")
    order_items = db.relationship("OrderItem", back_populates="product")
    
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
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer = db.relationship('User', back_populates='carts')
    cart_items = db.relationship("CartItem", back_populates="cart")
    
class CartItem(db.Model):
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.cart_id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    quantity = db.Column(db.Integer)
    cart = db.relationship('Cart', back_populates='cart_items')
    product = db.relationship('Product', back_populates='cart_items')
    
class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    order_status = db.Column(db.String(20), default="processing")  # Default value can be set as needed
    placed_date = db.Column(db.Date)
    shipped_date = db.Column(db.Date)
    delivered_date = db.Column(db.Date)
    customer = db.relationship('User', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order')

class OrderItem(db.Model):
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    quantity = db.Column(db.Integer)
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')