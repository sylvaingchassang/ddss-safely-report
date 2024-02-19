from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from safely_report.auth.utils import logout_and_clear, role_required
from safely_report.models import GlobalState, Respondent, Role, User, db
from safely_report.settings import XLSFORM_PATH
from safely_report.survey.form_generator import SurveyFormGenerator
from safely_report.survey.garbling import Garbler
from safely_report.survey.survey_processor import SurveyProcessor

# Instantiate classes for conducting the survey
survey_processor = SurveyProcessor(XLSFORM_PATH, session)
garbler = Garbler(XLSFORM_PATH, db)
form_generator = SurveyFormGenerator(survey_processor, garbler)


survey_blueprint = Blueprint("survey", __name__)


@survey_blueprint.before_request
@login_required
def require_auth():
    pass  # Actual implementation handled by decorator


@survey_blueprint.before_request
def handle_nonactive_survey():
    if not GlobalState.is_survey_active():
        if current_user.role == Role.Respondent:
            current_app.logger.warning(
                "Access attempted at non-active survey "
                f"- user {current_user.id}"
            )
            # TODO: Flash message and redirect
            return "Survey is currently unavailable"


@survey_blueprint.context_processor
def inject_template_variables():
    return {"is_testing_mode": current_user.role != Role.Respondent}


@survey_blueprint.errorhandler(IntegrityError)
def handle_response_resubmission(e):
    current_app.logger.warning(f"Resubmission tried - user {current_user.id}")
    flash("Response had already been submitted.", "error")
    return redirect(request.referrer or url_for("survey.index"))


@survey_blueprint.errorhandler(StaleDataError)
def handle_concurrency_conflict(e):
    current_app.logger.warning(
        "Failed submission due to concurrency conflict "
        "- user {current_user.id}"
    )
    flash("Sorry, we missed your submission. Please try again.", "warning")
    return redirect(request.referrer or url_for("survey.index"))


@survey_blueprint.route("/", methods=["GET", "POST"])
def index():
    if survey_processor.curr_survey_end:
        return render_template("survey/submit.html")

    if survey_processor.curr_survey_start:
        survey_processor.next()  # Roll forward to first displayable element

    form = form_generator.make_curr_form()

    if form.validate_on_submit():
        survey_processor.next()
        return redirect(url_for("survey.index"))

    return render_template("survey/index.html", form=form)


@survey_blueprint.route("/back")
def back():
    # Ensure full "refresh" by moving back twice and forward once
    survey_processor.back()
    if not survey_processor.curr_survey_start:
        survey_processor.back()
    survey_processor.next()

    return redirect(url_for("survey.index"))


@survey_blueprint.route("/exit")
def exit():
    if current_user.role == Role.Respondent:
        id = current_user.id
        logout_and_clear()
        current_app.logger.info(f"Survey exit - user {id}")
    else:
        survey_processor.clear_data()

    return redirect(url_for("index"))


@survey_blueprint.route("/submit")
def submit():
    if not survey_processor.curr_survey_end:
        return redirect(url_for("survey.index"))

    if current_user.role != Role.Respondent:
        survey_processor.clear_data()
        return redirect(url_for("index"))  # TODO: Flash message

    garbler.garble_and_store(
        survey_response=survey_processor.gather_survey_response(),
        respondent_uuid=current_user.uuid,
        enumerator_uuid=survey_processor.enumerator_uuid,
    )

    current_app.logger.info(f"Response submitted - user {current_user.id}")

    logout_and_clear()

    return "Survey response submitted"  # TODO: Flash message and redirect


@role_required(Role.Enumerator)
@survey_blueprint.route("/on-behalf-of/<respondent_id>")
def on_behalf_of(respondent_id: int):
    """
    Let enumerator access survey on behalf of their assigned respondent.
    """
    enumerator_uuid = current_user.uuid

    respondent = Respondent.query.filter_by(id=respondent_id).first()
    if respondent is not None:
        if respondent.enumerator_uuid == enumerator_uuid:
            user = User.query.filter_by(uuid=respondent.uuid).first()
            if user is not None:
                logout_and_clear()
                login_user(user)
                survey_processor.set_enumerator_uuid(enumerator_uuid)
                current_app.logger.info(f"Delegated login for user {user.id}")
                return redirect(url_for("survey.index"))

    current_app.logger.warning(f"Failed delegated login for user {user.id}")
    return "Respondent not found"  # TODO: Flash message and redirect
