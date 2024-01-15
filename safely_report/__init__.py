from flask import Flask
from flask_admin import Admin
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

from safely_report.admin.views import (
    EnumeratorModelView,
    RespondentModelView,
    SurveyAdminIndexView,
)
from safely_report.auth.views import auth_blueprint
from safely_report.enumerator.views import enumerator_blueprint
from safely_report.models import Enumerator, Respondent, User, db
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

    # Enable CSRF protection globally
    CSRFProtect(app)

    # Set up authentication
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.index"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.filter_by(id=user_id).first()

    # Set up admin interface
    admin = Admin(app, name="Safely Report", index_view=SurveyAdminIndexView())
    admin.add_view(
        RespondentModelView(
            Respondent, db.session, name="Respondents", endpoint="respondents"
        )
    )
    admin.add_view(
        EnumeratorModelView(
            Enumerator, db.session, name="Enumerators", endpoint="enumerators"
        )
    )

    # Register routes (i.e., "views")
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(enumerator_blueprint, url_prefix="/enumerator")
    app.register_blueprint(survey_blueprint, url_prefix="/survey")

    return app
