from dotenv import load_dotenv
from flask import Flask, render_template, redirect
from pyxform import builder, xls2json

from survey_processor import SurveyProcessor


load_dotenv()

app = Flask(__name__)
app.config.from_prefixed_env(prefix="FLASK")

# Parse survey form and pass it to processor
json_survey = xls2json.parse_file_to_json(app.config["XLSFORM_PATH"])
survey = builder.create_survey_element_from_dict(json_survey)
survey_processor = SurveyProcessor(survey)

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
