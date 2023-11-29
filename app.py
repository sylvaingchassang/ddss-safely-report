from dotenv import load_dotenv
from flask import Flask, redirect, render_template, session, url_for
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

from form_generator import SurveyFormGenerator
from survey_processor import SurveyProcessor
from utils import serialize_dict

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


# Construct survey processor and form generator
path_to_xlsform = app.config["XLSFORM_PATH"]
survey_processor = SurveyProcessor(path_to_xlsform, session)
form_generator = SurveyFormGenerator(survey_processor)


@app.route("/")
def index():
    return "Welcome!"


@app.route("/survey", methods=["GET", "POST"])
def survey():
    if survey_processor.curr_survey_end:
        return redirect(url_for("submit"))

    if survey_processor.curr_survey_start:
        survey_processor.next()  # Roll forward to first displayable element

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
    # Ensure full "refresh" by moving back twice and forward once
    survey_processor.back()
    if not survey_processor.curr_survey_start:
        survey_processor.back()
    survey_processor.next()

    return redirect(url_for("survey"))


@app.route("/survey/submit")
def submit():
    if not survey_processor.curr_survey_end:
        return redirect(url_for("survey"))

    # Store survey response into database
    try:
        response_dict = survey_processor.gather_responses_to_store()
        response_serialized = serialize_dict(response_dict)
        response_record = Response(response=response_serialized)
        db.session.add(response_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return e

    # Clear session data if response has been successfully stored in database
    survey_processor.clear_session()

    return "Survey response submitted"


if __name__ == "__main__":
    app.run(debug=True)
