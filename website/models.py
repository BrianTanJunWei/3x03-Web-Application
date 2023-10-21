from . import db
from flask_login import UserMixin 
from sqlalchemy.sql import func
from PIL import Image
from werkzeug.utils import secure_filename
from flask import request, current_app
import os

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f"Product('{self.name}', '{self.price}')"