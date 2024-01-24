from flask import redirect, url_for
from flask_login import current_user

from safely_report import create_app
from safely_report.models import Enumerator, Respondent, Role, User
from safely_report.scheduler import scheduler

app = create_app()


@app.before_request
def pre_populate_database():
    if not app.config.get("DATABASE_PREPOPULATED"):
        User.init_admin()
        Respondent.pre_populate()
        Enumerator.pre_populate()
        app.config["DATABASE_PREPOPULATED"] = True


@app.before_request
def start_scheduler():
    if not app.config.get("SCHEDULER_STARTED"):
        scheduler.start()
        app.config["SCHEDULER_STARTED"] = True


@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == Role.Respondent:
            return redirect(url_for("survey.index"))
        elif current_user.role == Role.Enumerator:
            return redirect(url_for("enumerator.index"))
        elif current_user.role == Role.Admin:
            return redirect(url_for("admin.index"))

    return redirect(url_for("auth.index"))


if __name__ == "__main__":
    app.run(debug=True)
