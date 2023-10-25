import unittest
from website import create_app, db
from website.models import User
from flask_testing import TestCase
import logging
from website.auth import bcrypt

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
        user = User(email='testuser@example.com', first_name='Test', password=hashed_password)
        db.session.add(user)
        db.session.commit()


    def test_login(self):
        response = self.client.post('/login', data=dict(
            email='testuser@example.com',
            password='password'
        ), follow_redirects=True)
        logging.info("Password used: password")
        logging.info(f"User password: {User.query.first().password}")

        self.assert200(response)  # Check if the response is successful
        self.assertIn(b'Logged in successfully!', response.data)  # Check if the success flash message is in the response

    def test_login_invalid_credentials(self):
        response = self.client.post('/login', data=dict(
            email='testuser@example.com',
            password='wrong_password'
        ), follow_redirects=True)

        self.assert200(response)
        self.assertIn(b'Incorrect email or password. Try again', response.data)

    def test_signup(self):
        response = self.client.post('/sign-up', data=dict(
            email='newuser@example.com',
            firstName='New User',
            password1='new_password',
            password2='new_password'
        ), follow_redirects=True)

        self.assert200(response)
        self.assertIn(b'Sign up completed!', response.data)

if __name__ == '__main__':
    unittest.main()
