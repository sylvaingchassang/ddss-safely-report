from dotenv import load_dotenv
from flask import Flask, redirect, render_template, session
from flask_session import Session
from pyxform import builder, xls2json

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

# Parse survey form and pass it to processor
json_survey = xls2json.parse_file_to_json(
    path=app.config["XLSFORM_PATH"], default_name="__survey__"
)
survey = builder.create_survey_element_from_dict(json_survey)
survey_session = SurveySession(session)
survey_processor = SurveyProcessor(survey, survey_session)


@app.route("/")
def index():
    return "Welcome!"


@app.route("/survey")
def survey():
    return render_template("survey.html", survey_processor=survey_processor)


@app.route("/survey/next")
def next():
    survey_processor.next()
    return redirect("/survey")


@app.route("/survey/back")
def back():
    survey_processor.back()
    return redirect("/survey")


if __name__ == "__main__":
    app.run(debug=True)
