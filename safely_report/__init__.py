from flask import Flask, session
from flask_migrate import Migrate
from flask_session import Session

from safely_report.models import db
from safely_report.survey.form_generator import SurveyFormGenerator
from safely_report.survey.garbling import Garbler
from safely_report.survey.survey_processor import SurveyProcessor
from safely_report.survey.survey_session import SurveySession

# Create and configure app
app = Flask(__name__)
app.config.from_pyfile("settings.py")

# Set up use of server-side sessions
Session(app)

# Set up database
db.init_app(app)
Migrate(app, db)

# Instantiate classes for conducting the survey
path_to_xlsform = app.config["XLSFORM_PATH"]
survey_session = SurveySession(session)
survey_processor = SurveyProcessor(path_to_xlsform, survey_session)
garbler = Garbler(path_to_xlsform, survey_session, db)
form_generator = SurveyFormGenerator(survey_processor)

from safely_report.survey.views import survey_blueprint  # noqa

# Register routes (i.e., "views")
app.register_blueprint(survey_blueprint, url_prefix="/survey")
