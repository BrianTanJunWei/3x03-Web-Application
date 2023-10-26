from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from dotenv import load_dotenv
import os

db = SQLAlchemy()
DB_NAME = "database.db"
load_dotenv()  # Load environment variables from .env file

SECRET_KEY = os.getenv('SECRET_KEY')
TEST_STRIPE_SECRET_KEY = os.getenv('TEST_STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['TEST_STRIPE_SECRET_KEY'] = TEST_STRIPE_SECRET_KEY
    app.config['STRIPE_PUBLIC_KEY'] = STRIPE_PUBLIC_KEY

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = 'uploads'

    db.init_app(app)
   
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Product

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' # specify where to go when user not logged in 
    login_manager.init_app(app)

    # tell flask how we load user
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id)) # primary key

    return app


def create_database(app):
    with app.app_context():
        db_path = path.join('website', DB_NAME)
        if not path.exists(db_path): 
            db.create_all()
            print('Created Database!')
