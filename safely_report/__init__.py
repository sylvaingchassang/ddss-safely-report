from flask import Flask
from flask_migrate import Migrate
from flask_session import Session

from safely_report.admin import admin
from safely_report.auth import login_manager
from safely_report.auth.views import auth_blueprint
from safely_report.enumerator.views import enumerator_blueprint
from safely_report.models import db
from safely_report.scheduler import scheduler
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

    # Set up scheduler
    scheduler.init_app(app)

    # Set up authentication
    login_manager.init_app(app)

    # Set up admin interface
    admin.init_app(app)

    # Register routes (i.e., "views")
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(enumerator_blueprint, url_prefix="/enumerator")
    app.register_blueprint(survey_blueprint, url_prefix="/survey")

    return app
