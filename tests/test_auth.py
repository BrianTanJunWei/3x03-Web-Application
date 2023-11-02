import unittest
from website import create_app, db
from website.models import Login, UserAccounts
from flask_testing import TestCase
from website.auth import bcrypt
from flask_login import login_user, current_user

class TestAuth(TestCase):
    def create_app(self):
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # Use a separate test database
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF protection for testing
        return app

    def setUp(self):
        db.create_all()
        self.client = self.app.test_client()
        self._create_test_user()

    def tearDown(self):
        db.drop_all()

    def _create_test_user(self):
        # Create a test user for login and signup tests
        hashed_password = bcrypt.generate_password_hash('password').decode('utf-8')
        user_login = Login(email_address='testuser1@example.com', password=hashed_password, account_status=True, account_type=2)
        user_accounts = UserAccounts(email_address='testuser1@example.com', first_name='Test', last_name='User')
        db.session.add(user_login)
        db.session.add(user_accounts)
        db.session.commit()

    def test_login(self):
        response = self.client.post('/login', data=dict(
            email='testuser1@example.com',
            password='password'
        ), follow_redirects=True)

        self.assert200(response)  # Check if the response is successful
        self.assertTrue(current_user.is_authenticated)  # Check if the user is authenticated
        # Check if the user is redirected to a specific page after login
        self.assertEqual(response.request.path, '/')
        
    def test_login_invalid_credentials(self):
        response = self.client.post('/login', data=dict(
            email='testuser1@example.com',
            password='wrong_password'
        ), follow_redirects=True)

        self.assert200(response)
        self.assertIn(b'Incorrect email or password. Try again', response.data)
        self.assertFalse(current_user.is_authenticated)  # Check if the user is not authenticated

    def test_signup(self):
        response = self.client.post('/sign-up', data=dict(
            email='newuser1@example.com',
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

if __name__ == '__main__':
    unittest.main()
