from safely_report import create_app
from safely_report.models import Enumerator, Respondent, add_data_from_csv
from safely_report.settings import (
    ENUMERATOR_ROSTER_PATH,
    RESPONDENT_ROSTER_PATH,
)

app = create_app()


@app.before_request
def pre_populate_database():
    if not app.config.get("PREPOPULATED"):
        if Respondent.query.first() is None:
            add_data_from_csv(Respondent, RESPONDENT_ROSTER_PATH)
        if Enumerator.query.first() is None:
            add_data_from_csv(Enumerator, ENUMERATOR_ROSTER_PATH)
        app.config["PREPOPULATED"] = True


@app.route("/")
def index():
    return "Welcome!"


if __name__ == "__main__":
    app.run(debug=True)
