from csv import DictReader

from safely_report import create_app
from safely_report.models import Enumerator, Respondent, db
from safely_report.settings import (
    ENUMERATOR_ROSTER_PATH,
    RESPONDENT_ROSTER_PATH,
)

app = create_app()


@app.before_request
def pre_populate_database():
    if not app.config.get("PREPOPULATED"):
        if Respondent.query.first() is None:
            with open(RESPONDENT_ROSTER_PATH, "r") as file:
                csv_reader = DictReader(file)
                for row in csv_reader:
                    db.session.add(Respondent(**row))
            db.session.commit()
        if Enumerator.query.first() is None:
            with open(ENUMERATOR_ROSTER_PATH, "r") as file:
                csv_reader = DictReader(file)
                for row in csv_reader:
                    db.session.add(Enumerator(**row))
            db.session.commit()
        app.config["PREPOPULATED"] = True


@app.route("/")
def index():
    return "Welcome!"


if __name__ == "__main__":
    app.run(debug=True)
