from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

from safely_report.models import Role, User

auth_blueprint = Blueprint("auth", __name__, template_folder="templates/auth")


def make_auth_form(label: str) -> FlaskForm:
    class AuthForm(FlaskForm):
        field = PasswordField(label, validators=[DataRequired()])
        submit = SubmitField("Submit")

    return AuthForm()


@auth_blueprint.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == Role.Respondent:
            return redirect(url_for("survey.index"))
    return render_template("select_role.html")


@auth_blueprint.route("/login/respondent", methods=["GET", "POST"])
def login_respondent():
    form = make_auth_form("Please enter your UUID:")

    if form.validate_on_submit():
        uuid = form.field.data
        user = User.query.get(uuid)
        if user is not None and user.role == Role.Respondent:
            login_user(user)
            return redirect(url_for("survey.index"))
        return "Respondent not found"  # TODO: Replace with flash message

    return render_template("authenticate.html", form=form)


@auth_blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.index"))
