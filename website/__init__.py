from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from dotenv import load_dotenv
import os

db = SQLAlchemy()
DB_NAME = "3x03_Database"
load_dotenv()  # Load environment variables from .env file

SECRET_KEY = os.getenv('SECRET_KEY')
TEST_STRIPE_SECRET_KEY = os.getenv('TEST_STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
SENDINBLUE_API_KEY = os.getenv('SENDINBLUE_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
DATABASE_NAME = os.getenv('DATABASE_NAME')

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['TEST_STRIPE_SECRET_KEY'] = TEST_STRIPE_SECRET_KEY
    app.config['STRIPE_PUBLIC_KEY'] = STRIPE_PUBLIC_KEY
    app.config['SENDINBLUE_API_KEY'] = SENDINBLUE_API_KEY
    app.config['SENDER_EMAIL'] = SENDER_EMAIL
    app.config['DATABASE_NAME'] = DATABASE_NAME

    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://root:3x03_gpa5@172.18.0.5:3306/{DATABASE_NAME}'
    app.config['UPLOAD_FOLDER'] = 'uploads'

    db.init_app(app)
   
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import Login, UserAccounts, AdminAccounts, StaffAccounts, Product

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' # specify where to go when user not logged in 
    login_manager.init_app(app)

    # tell flask how we load user
    @login_manager.user_loader
    def load_user(id):
        return Login.query.get(int(id)) # primary key
    
    def return_user_name(id):
        user = Login.query.get(int(id))
        if (user.account_type == 0):
            name = AdminAccounts.query.filter_by(email_address=user.email_address).first()
            return name.name
        if (user.account_type == 1):
            name = StaffAccounts.query.filter_by(email_address=user.email_address).first()
            return name.name
        if (user.account_type == 2):

            name = UserAccounts.query.filter_by(email_address=user.email_address).first()
            return name.first_name
        
    
    def return_user_type(id):
        user = Login.query.get(int(id))
        return user.account_type

    app.jinja_env.globals.update(return_user_name=return_user_name,
                                 return_user_type=return_user_type)
    return app


def create_database(app):
    with app.app_context():
        db_path = path.join('website', DB_NAME)
        db.create_all()
        if not path.exists(db_path): 
            db.create_all()
            print('Created Database!')

