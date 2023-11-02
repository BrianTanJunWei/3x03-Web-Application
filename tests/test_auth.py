import os
import unittest
from website import create_app, db
from website.models import Login, UserAccounts
from flask_testing import TestCase
from website.auth import bcrypt
from flask_login import current_user

DATABASE_TEST_NAME = os.getenv('DATABASE_TEST_NAME')

class TestAuth(TestCase):
    def create_app(self):
        app = create_app()
        app.config['DATABASE_TEST_NAME'] = DATABASE_TEST_NAME
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://root:3x03_gpa5@172.18.0.3:3306/{DATABASE_TEST_NAME}'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF protection for testing
        return app

    def setUp(self):
        db.create_all()
        self.client = self.app.test_client()
        self._create_test_user()

    def _create_test_user(self):
        hashed_password = bcrypt.generate_password_hash('password').decode('utf-8')
        self.user_email = f'testing{self._testMethodName}@example.com'
        user_login = Login(email_address=self.user_email, password=hashed_password, account_status=True, account_type=2)
        user_accounts = UserAccounts(email_address=self.user_email, first_name='Test', last_name='User')
        db.session.add(user_login)
        db.session.add(user_accounts)
        db.session.commit()

    def test_login(self):
        response = self.client.post('/login', data=dict(
            email_address='testing@example.com',
            password='password'
        ), follow_redirects=True)

        self.assert200(response)  # Check if the response is successful
        self.assertTrue(current_user.is_authenticated)  # Check if the user is authenticated
        # Check if the user is redirected to a specific page after login
        self.assertEqual(response.request.path, '/')
        
    def test_login_invalid_credentials(self):
        response = self.client.post('/login', data=dict(
            email_address='testing@example.com',
            password='wrong_password'
        ), follow_redirects=True)

        self.assert200(response)
        self.assertIn(b'Incorrect email or password. Try again', response.data)
        self.assertFalse(current_user.is_authenticated)  # Check if the user is not authenticated

    def test_signup(self):
        response = self.client.post('/sign-up', data=dict(
            email='newuser@example.com',
            firstName='New User',
            lastName='Last Name',
            address='123 Main St',
            contact='1234567890',
            password1='new_password',
            password2='new_password'
        ), follow_redirects=True)

        self.assert200(response)
        self.assertIn(b'Sign up completed!', response.data)
        self.assertTrue(current_user.is_authenticated)  # Check if the user is authenticated

def tearDown(self):
    db.session.remove()
    
    # First, delete records from the child table (user_accounts)
    user_accounts_to_delete = UserAccounts.query.filter_by(email_address='testing@example.com').all()
    for user_account in user_accounts_to_delete:
        db.session.delete(user_account)
        db.session.commit()

    # Then, delete the record from the parent table (login)
    user_to_delete = Login.query.filter_by(email_address='testing@example.com').first()
    if user_to_delete:
        print(f"Deleting user: {user_to_delete.email_address}")
        db.session.delete(user_to_delete)
        print("User marked for deletion.")
        db.session.commit()
        print("User deleted successfully.")
    else:
        print("User not found in the database.")
