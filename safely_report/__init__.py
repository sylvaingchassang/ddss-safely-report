import logging

from flask import Flask, current_app, redirect, url_for
from flask_login import current_user
from flask_migrate import Migrate
from flask_session import Session

from safely_report.admin import admin
from safely_report.auth import login_manager
from safely_report.auth.views import auth_blueprint
from safely_report.enumerator.views import enumerator_blueprint
from safely_report.models import (
    Enumerator,
    GlobalState,
    Respondent,
    Role,
    User,
    db,
)
from safely_report.scheduler import scheduler
from safely_report.survey.views import survey_blueprint


def create_app() -> Flask:
    # Create and configure app
    app = Flask(__name__)
    app.config.from_pyfile("settings.py")

    # Configure logging
    if not app.debug:
        app.logger.setLevel(logging.INFO)

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

    # Set up routes (i.e., "views")
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(enumerator_blueprint, url_prefix="/enumerator")
    app.register_blueprint(survey_blueprint, url_prefix="/survey")

    # Set up root index view
    app.add_url_rule(rule="/", view_func=index)

    # Set up hooks
    app.before_request(_pre_populate_database)
    app.before_request(_start_scheduler)
    app.context_processor(_inject_template_variables)

    return app


def index():
    if current_user.is_authenticated:
        if current_user.role == Role.Respondent:
            return redirect(url_for("survey.index"))
        elif current_user.role == Role.Enumerator:
            return redirect(url_for("enumerator.index"))
        elif current_user.role == Role.Admin:
            return redirect(url_for("admin.index"))

    return redirect(url_for("auth.index"))


def _pre_populate_database():
    if not current_app.config.get("DATABASE_PREPOPULATED"):
        GlobalState.init()
        User.init_admin()
        Respondent.pre_populate()
        Enumerator.pre_populate()
        current_app.config["DATABASE_PREPOPULATED"] = True


def _start_scheduler():
    if not current_app.config.get("SCHEDULER_STARTED"):
        scheduler.start()
        current_app.config["SCHEDULER_STARTED"] = True


def _inject_template_variables():
    return {
        "is_survey_active": GlobalState.is_survey_active(),
        "is_survey_paused": GlobalState.is_survey_paused(),
        "is_survey_ended": GlobalState.is_survey_ended(),
    }
