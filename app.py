from flask import redirect, url_for

from safely_report import create_app
from safely_report.models import Enumerator, Respondent
from safely_report.settings import (
    ENUMERATOR_ROSTER_PATH,
    RESPONDENT_ROSTER_PATH,
)

app = create_app()


@app.before_request
def pre_populate_database():
    if not app.config.get("PREPOPULATED"):
        if Respondent.query.first() is None:
            Respondent.add_data_from_csv(RESPONDENT_ROSTER_PATH)
        if Enumerator.query.first() is None:
            Enumerator.add_data_from_csv(ENUMERATOR_ROSTER_PATH)
        app.config["PREPOPULATED"] = True


@app.route("/")
def index():
    return redirect(url_for("auth.index"))


if __name__ == "__main__":
    app.run(debug=True)
