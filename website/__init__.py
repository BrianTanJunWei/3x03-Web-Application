from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
load_dotenv()  # Load environment variables from .env file

SECRET_KEY = os.getenv('SECRET_KEY')
TEST_STRIPE_SECRET_KEY = os.getenv('TEST_STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
SENDINBLUE_API_KEY = os.getenv('SENDINBLUE_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
DATABASE_NAME = os.getenv('DATABASE_NAME')
# DATABASE_TEST_NAME = os.getenv('DATABASE_TEST_NAME')
DATABASE_TEST_NAME = 'test_db'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    csrf = CSRFProtect(app)
    app.config['TEST_STRIPE_SECRET_KEY'] = TEST_STRIPE_SECRET_KEY
    app.config['STRIPE_PUBLIC_KEY'] = STRIPE_PUBLIC_KEY
    app.config['SENDINBLUE_API_KEY'] = SENDINBLUE_API_KEY
    app.config['SENDER_EMAIL'] = SENDER_EMAIL
    app.config['DATABASE_NAME'] = DATABASE_NAME
    app.config['DATABASE_TEST_NAME'] = DATABASE_TEST_NAME

    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    if app.config['TESTING']:
        #Use the testing database URI with localhost
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://root:3x03_gpa5@172.18.0.3:3306/{DATABASE_TEST_NAME}'
    else:
        # Use the production database URI (MySQL)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://root:3x03_gpa5@172.18.0.3:3306/{DATABASE_NAME}'

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

    # Implementing the CSP for the entire application
    @app.after_request
    def apply_csp(response):
        csp = ("default-src 'self'; "
               "script-src 'self' "
               "'sha256-DTs+PYu3AWGO37Cjpl9SMn2tpiIWVPMBIMnbyJ7dEK4=' "
               "'sha256-F9sK+B8DQLklcA7ODBaGvWpvpj+6mv2UNA33p3J2D88=' "
               "'sha256-m+pWPJK/WXg1QY7IloTEfEeSdGqc7WcI7GfMyxFyXvc=' "
               "'sha256-l7zFrRVV2XIn0Noa9R/8RUgL5aErbMiOYycrLARV2WI=' "
               "'sha256-YazMb6d9LlJhtWUCUEqhr5nGeGBn8/UgnFqfXKjMvEU=' "
               "'sha256-iIwGmYnLAxqJ9aTluVaHSFy2xapfECgFhPOaHvoyiug=' "
               "'sha256-p73cl0+wpizOKMLvme3V5bcBOb8pnKwIAwGL0twzAyY=' "
               "'sha256-45dx55iN65eXM31bMEQr0SNtwmMIbCiC2h/KXVAc2CI=' "
               "'sha256-sj4H/w3l1rLF4o4HDUxiGBsldUBlHkXZzV2HeI3DLBU=' "
               "'sha256-FX8235gJW4NfTQvlMSxUxRLR2a6of/vWYbvCqoQ+01Y=' "
               "'sha256-GrhWpnP7HaL3yxOiVuUfq/Oe4fUb70UfRmrKcs6gUQA=' "
               "'sha256-oYNA+j/2zvOc/bV8U58C6uwdGVbOueg43tGQBzrBkxs=' "
               "'sha256-NRH8uVC2oe41yrxd1YxM17Ce2GMcuj5g57xlJX8QIK8=' "
               "'sha256-J/BzYshaL+ipBid4iT+RcJ3tGGgqh2v2jEjTVOQMdLk=' "
               "'sha256-Yn+8E9m9dfx784N0ub31YPPjXpZAxISC/2u6nSf/e1U=' "
               "'sha256-lGi7JLwLuFkHTQv9af4Piz4WgISXBJalluLJfxIg9Uw=' "
               "'sha256-jichvIS/MjoQc32Q6T4WTA2pW3k6VFoK3wguBBYzNzE=' "
               "'sha256-yXbNnMAsbCgxYWlAl97nHRJw4m8uGOUrjbQ8ucYL00E=' "
               "https://code.jquery.com "
               "https://cdnjs.cloudflare.com "
               "https://maxcdn.bootstrapcdn.com "
               "https://js.stripe.com; "  # Corrected the placement
               "style-src 'self' "
               "'sha256-Yj4TLpFHtiSpvQ17hJF/aVRvNZ2/UmX/SYOyXdIV+t4=' "
               "'sha256-l56jCYlJ06Hx0CV4M+e8ayvL+lw7y9QSVGVj33GGwz0=' "
               "'sha256-Qqdr7kYS9XQC7u6vWxkMToTP5f/uWFexOCoIjvSwcTg=' "
               "'sha256-biLFinpqYMtWHmXfkA1BPeCY0/fNt46SAZ+BBk5YUog=' "
               "https://stackpath.bootstrapcdn.com; "
               "font-src 'self' https://stackpath.bootstrapcdn.com; "
               "img-src 'self' data:;"
               "frame-src 'self' https://js.stripe.com;")
        response.headers['Content-Security-Policy'] = csp
        return response
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
        db_path = path.join('website', DATABASE_NAME)
        if not path.exists(db_path): 
            db.create_all()
            print('Created Database!')
