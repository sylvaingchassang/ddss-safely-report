from flask import redirect, url_for
from flask_login import current_user

from safely_report import create_app
from safely_report.models import Enumerator, Respondent, Role, User

app = create_app()


@app.before_request
def pre_populate_database():
    if not app.config.get("PREPOPULATED"):
        User.init_admin()
        Respondent.pre_populate()
        Enumerator.pre_populate()
        app.config["PREPOPULATED"] = True


@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == Role.Respondent:
            return redirect(url_for("survey.index"))
        if current_user.role == Role.Admin:
            return redirect(url_for("admin.index"))

    return redirect(url_for("auth.index"))


if __name__ == "__main__":
    app.run(debug=True)
