from time import time

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


@app.before_request
def clear_expired_sessions():
    INTERVAL = app.config["PERMANENT_SESSION_LIFETIME"] // 3
    prev_time = app.config.get("LAST_CLEARED_AT", 0)
    curr_time = time()
    elapsed = curr_time - prev_time
    if elapsed > INTERVAL:
        app.session_interface.cache._remove_expired(curr_time)
        app.config["LAST_CLEARED_AT"] = curr_time


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
