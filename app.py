from dotenv import load_dotenv
from flask import Flask, redirect, render_template, session, url_for
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from pyxform import builder, xls2json

from form_generator import SurveyFormGenerator
from survey_processor import SurveyProcessor
from survey_session import SurveySession

load_dotenv()

app = Flask(__name__)
app.config.from_prefixed_env(prefix="FLASK")

# Set up use of server-side sessions
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = ".flask_sessions"
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_PERMANENT"] = False
Session(app)

# Set up database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Migrate(app, db)


# TODO: Modularize into `models.py` when reorganizing app files
class Response(db.Model):  # type: ignore
    __tablename__ = "responses"

    id = db.Column(db.Integer, primary_key=True)
    response = db.Column(db.String(), nullable=False)  # Stringified JSON

    def __init__(self, response):
        self.response = response

    def __repr__(self):
        return f"<Response ID: {self.id}>"


# Parse survey form and pass it to processor
survey_json = xls2json.parse_file_to_json(
    path=app.config["XLSFORM_PATH"], default_name="__survey__"
)
survey_tree = builder.create_survey_element_from_dict(survey_json)
survey_session = SurveySession(session)
survey_processor = SurveyProcessor(survey_tree, survey_session)
form_generator = SurveyFormGenerator(survey_processor)


@app.route("/")
def index():
    return "Welcome!"


@app.route("/survey", methods=["GET", "POST"])
def survey():
    if survey_processor.survey_end_reached:
        return redirect(url_for("submit"))

    form = form_generator.make_curr_form()

    if form.validate_on_submit():
        survey_processor.next()
        return redirect(url_for("survey"))

    return render_template(
        "survey.html",
        form=form,
        survey_processor=survey_processor,
    )


@app.route("/survey/back")
def back():
    survey_processor.back()
    return redirect(url_for("survey"))


@app.route("/survey/submit")
def submit():
    return "Confirm or cancel response submission"


if __name__ == "__main__":
    app.run(debug=True)
