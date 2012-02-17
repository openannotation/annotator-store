from . import TestCase, helpers as h
import re

from annotator.model import User

from flask import current_app, url_for

class TestUser(TestCase):
    def setup(self):
        super(TestUser, self).setup()
        self.cli = self.app.test_client()

        self.user = User('test', 'test@example.com', 'password')
        h.db_save(self.user)

    def login(self):
        with self.cli.session_transaction() as sess:
            sess['user'] = 'test'

    def logout(self):
        with self.cli.session_transaction() as sess:
            del sess['user']

    def test_home_logged_out(self):
        """Redirect to login if logged out"""
        resp = self.cli.get(url_for('user.home'))
        h.assert_in('Location', resp.headers)
        h.assert_true(resp.headers['Location'].endswith(url_for('user.login')))

    def test_login_logged_out(self):
        """Ask for relevant details to log in"""
        resp = self.cli.get(url_for('user.login'))
        h.assert_in("Username/email", resp.data)
        h.assert_in("Password", resp.data)

    def test_reset_password_request(self):
        """Ask for username or email address"""
        resp = self.cli.get(url_for('user.reset_password_request'))
        h.assert_in("Username/email", resp.data)

    def test_reset_password_request_logged_in(self):
        """Don't allow logged in users to reset passwords using this form"""
        self.login()
        resp = self.cli.get(url_for('user.reset_password_request'))
        h.assert_in('Location', resp.headers)
        h.assert_true(resp.headers['Location'].endswith(url_for('user.home')))

    def test_reset_password(self):
        """Send email if user in database"""
        mail = current_app.extensions['mail']
        with mail.record_messages() as outbox:
            self.cli.post(url_for('user.reset_password_request'),
                          data={'login': 'test@example.com'})
            h.assert_equal(len(outbox), 1)
            h.assert_equal(outbox[0].subject, 'Reset password')
            body = outbox[0].body

        code_re = re.compile(r'reset_password/(\S+)')
        code = code_re.search(body).group(1)

        # Make request to reset_password, and check get password form if
        # code correct:

        resp = self.cli.get(url_for('user.reset_password', code=code))
        h.assert_in('New password', resp.data)

        # Make request to reset_password and check get redirect if code
        # incorrect:

        resp = self.cli.get(url_for('user.reset_password', code='test.ABC'))
        h.assert_in('Location', resp.headers)
        h.assert_true(resp.headers['Location'].endswith(url_for('user.reset_password_request')))

        # Post correct reset_password form and ensure user's password gets
        # changed

        resp = self.cli.post(url_for('user.reset_password', code=code),
                                     data={'password': 'mynewpassword',
                                           'confirm': 'mynewpassword'})
        u = User.query.filter_by(username='test').first()
        h.assert_true(u.check_password('mynewpassword'))

        # Post incorrect reset_password form and ensure user's password doesn't
        # change

        resp = self.cli.post(url_for('user.reset_password', code='test.ABC'),
                                     data={'password': 'foopassword',
                                           'confirm': 'foopassword'})
        u = User.query.filter_by(username='test').first()
        h.assert_false(u.check_password('foopassword'))
