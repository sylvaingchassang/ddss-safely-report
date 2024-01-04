from flask import Blueprint, redirect, url_for
from flask_login import current_user, login_required, login_user, logout_user

from safely_report.models import Role, User

auth_blueprint = Blueprint("auth", __name__, template_folder="templates/auth")


@auth_blueprint.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == Role.Respondent:
            return redirect(url_for("survey.index"))
    return "Please log in"


@auth_blueprint.route("/login/respondent/<uuid>")
def login_respondent(uuid):
    user = User.query.get(uuid)
    if user is not None and user.role == Role.Respondent:
        login_user(user)
        return redirect(url_for("survey.index"))
    return "Respondent not found"


@auth_blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.index"))
