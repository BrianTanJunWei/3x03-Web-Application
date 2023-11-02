import unittest
from flask import current_app
from website import create_app, db
from website.models import Login, UserAccounts
from website.auth import bcrypt

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self._create_test_user()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_test_user(self):
        hashed_password = bcrypt.generate_password_hash('password').decode('utf-8')
        user_login = Login(email_address='test@example.com', password=hashed_password, account_status=True, account_type=2)
        user_accounts = UserAccounts(email_address='test@example.com', first_name='Test', last_name='User')
        db.session.add(user_login)
        db.session.add(user_accounts)
        db.session.commit()

    def test_login_valid_credentials(self):
        response = self.client.post('/login', data=dict(
            email='test@example.com',
            password='password'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in as', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post('/login', data=dict(
            email='test@example.com',
            password='wrong_password'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Incorrect email or password', response.data)

    def test_registration_valid_input(self):
        response = self.client.post('/sign-up', data=dict(
            email='newuser@example.com',
            firstName='New User',
            lastName='Last Name',
            address='123 Main St',
            contact='1234567890',
            password1='new_password',
            password2='new_password'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign up completed', response.data)

    def test_registration_existing_email(self):
        response = self.client.post('/sign-up', data=dict(
            email='test@example.com',  # An existing email
            firstName='New User',
            lastName='Last Name',
            address='123 Main St',
            contact='1234567890',
            password1='new_password',
            password2='new_password'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email already exist', response.data)

    # You can add more test cases as needed

if __name__ == '__main__':
    unittest.main()
