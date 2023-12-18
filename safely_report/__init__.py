from flask import Flask
from flask_migrate import Migrate
from flask_session import Session

from safely_report.models import db
from safely_report.survey.views import survey_blueprint


def create_app() -> Flask:
    # Create and configure app
    app = Flask(__name__)
    app.config.from_pyfile("settings.py")

    # Set up use of server-side sessions
    Session(app)

    # Set up database
    db.init_app(app)
    Migrate(app, db)

    # Register routes (i.e., "views")
    app.register_blueprint(survey_blueprint, url_prefix="/survey")

    return app
