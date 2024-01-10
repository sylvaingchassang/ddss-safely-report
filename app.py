from flask import redirect, url_for

from safely_report import create_app
from safely_report.models import Enumerator, Respondent

app = create_app()


@app.before_request
def pre_populate_database():
    if not app.config.get("PREPOPULATED"):
        Respondent.pre_populate()
        Enumerator.pre_populate()
        app.config["PREPOPULATED"] = True


@app.route("/")
def index():
    return redirect(url_for("auth.index"))


if __name__ == "__main__":
    app.run(debug=True)
