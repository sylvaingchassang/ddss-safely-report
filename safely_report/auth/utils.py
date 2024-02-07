from functools import wraps

from flask import current_app, session
from flask_login import current_user, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

from safely_report.models import Role


def make_auth_form(label: str) -> FlaskForm:
    class AuthForm(FlaskForm):
        field = PasswordField(label, validators=[DataRequired()])
        submit = SubmitField("Submit")

    return AuthForm()


def logout_and_clear():
    """
    Log out and clear all session data.
    """
    logout_user()
    session.clear()


def role_required(role: Role):
    """
    A decorator that ensures a view is accessible
    only by users who have the specified role.
    """

    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if current_user.role != role:
                return current_app.login_manager.unauthorized()

        return decorated_view

    return decorator
