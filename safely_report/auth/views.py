from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

from safely_report.models import Role, User
from safely_report.settings import ADMIN_PASSWORD

auth_blueprint = Blueprint("auth", __name__)


def make_auth_form(label: str) -> FlaskForm:
    class AuthForm(FlaskForm):
        field = PasswordField(label, validators=[DataRequired()])
        submit = SubmitField("Submit")

    return AuthForm()


@auth_blueprint.route("/")
def index():
    return render_template("auth/index.html")


@auth_blueprint.route("/login/respondent", methods=["GET", "POST"])
def login_respondent():
    form = make_auth_form("Please enter your UUID:")

    if form.validate_on_submit():
        uuid = form.field.data
        user = User.query.filter_by(uuid=uuid).first()
        if user is not None and user.role == Role.Respondent:
            login_user(user)
            return redirect(url_for("survey.index"))
        return "Respondent not found"  # TODO: Flash message and redirect

    return render_template(
        "auth/submit.html",
        form=form,
        endpoint="auth.login_respondent",
    )


@auth_blueprint.route("/login/enumerator", methods=["GET", "POST"])
def login_enumerator():
    form = make_auth_form("Please enter your UUID:")

    if form.validate_on_submit():
        uuid = form.field.data
        user = User.query.filter_by(uuid=uuid).first()
        if user is not None and user.role == Role.Enumerator:
            login_user(user)
            return redirect(url_for("enum.index"))
        return "Enumerator not found"  # TODO: Flash message and redirect

    return render_template(
        "auth/submit.html",
        form=form,
        endpoint="auth.login_enumerator",
    )


@auth_blueprint.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    form = make_auth_form("Please enter admin password:")

    if form.validate_on_submit():
        password = form.field.data
        if password == ADMIN_PASSWORD:
            user = User.get_admin()
            login_user(user)
            return redirect(url_for("admin.index"))
        return "Invalid password"  # TODO: Flash message and redirect

    return render_template(
        "auth/submit.html",
        form=form,
        endpoint="auth.login_admin",
    )


@auth_blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.index"))
