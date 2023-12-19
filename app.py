from csv import DictReader

from safely_report import create_app
from safely_report.models import Respondent, db
from safely_report.settings import ROSTER_PATH

app = create_app()


@app.route("/")
def index():
    if Respondent.query.first() is None:
        with open(ROSTER_PATH, "r") as file:  # type: ignore
            csv_reader = DictReader(file)
            for row in csv_reader:
                db.session.add(Respondent(**row))
        db.session.commit()

    return "Welcome!"


if __name__ == "__main__":
    app.run(debug=True)
