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

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
   
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import Login, UserAccounts

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
        if not path.exists(db_path): 
            db.create_all()
            print('Created Database!')

