from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from safely_report.auth.utils import make_auth_form
from safely_report.models import Role, User
from safely_report.settings import ADMIN_PASSWORD

auth_blueprint = Blueprint("auth", __name__)


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
            current_app.logger.info(f"Login - user {user.id}")
            return redirect(url_for("survey.index"))
        current_app.logger.info(f"Failed login - user {user.id}")
        return "Respondent not found"  # TODO: Flash message and redirect

    return render_template("auth/submit.html", form=form)


@auth_blueprint.route("/login/enumerator", methods=["GET", "POST"])
def login_enumerator():
    form = make_auth_form("Please enter your UUID:")

    if form.validate_on_submit():
        uuid = form.field.data
        user = User.query.filter_by(uuid=uuid).first()
        if user is not None and user.role == Role.Enumerator:
            login_user(user)
            current_app.logger.info(f"Login - user {user.id}")
            return redirect(url_for("enumerator.index"))
        current_app.logger.info(f"Failed login - user {user.id}")
        return "Enumerator not found"  # TODO: Flash message and redirect

    return render_template("auth/submit.html", form=form)


@auth_blueprint.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    form = make_auth_form("Please enter admin password:")

    if form.validate_on_submit():
        password = form.field.data
        if password == ADMIN_PASSWORD:
            user = User.get_admin()
            login_user(user)
            current_app.logger.info(f"Login - user {user.id}")
            return redirect(url_for("admin.index"))
        current_app.logger.info(f"Failed login - user {user.id}")
        return "Invalid password"  # TODO: Flash message and redirect

    return render_template("auth/submit.html", form=form)


@auth_blueprint.route("/logout")
@login_required
def logout():
    id = current_user.id
    logout_user()
    session.clear()
    current_app.logger.info(f"Logout - user {id}")
    return redirect(url_for("auth.index"))
