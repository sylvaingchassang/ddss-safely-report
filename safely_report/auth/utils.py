from functools import wraps

from flask import current_app
from flask_login import current_user

from safely_report.models import Role


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
