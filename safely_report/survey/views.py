from flask import Blueprint, redirect, render_template, session, url_for
from flask_login import current_user, login_required

from safely_report.auth.utils import role_required
from safely_report.models import Role, db
from safely_report.settings import XLSFORM_PATH
from safely_report.survey.form_generator import SurveyFormGenerator
from safely_report.survey.garbling import Garbler
from safely_report.survey.survey_processor import SurveyProcessor
from safely_report.survey.survey_session import SurveySession

# Instantiate classes for conducting the survey
survey_session = SurveySession(session)
survey_processor = SurveyProcessor(XLSFORM_PATH, survey_session)
garbler = Garbler(XLSFORM_PATH, db)
form_generator = SurveyFormGenerator(survey_processor)


survey_blueprint = Blueprint("survey", __name__)


def curr_testing_mode() -> bool:
    if current_user.role == Role.Respondent:
        return False
    if current_user.role == Role.Enumerator and survey_session.respondent_uuid:
        return False
    return True


@survey_blueprint.before_request
@login_required
def require_auth():
    pass  # Actual implementation handled by decorator


@survey_blueprint.route("/", methods=["GET", "POST"])
def index():
    if survey_processor.curr_survey_end:
        return render_template(
            "survey/submit.html",
            curr_testing_mode=curr_testing_mode(),
        )

    if survey_processor.curr_survey_start:
        survey_processor.next()  # Roll forward to first displayable element

    form = form_generator.make_curr_form()

    if form.validate_on_submit():
        survey_processor.next()
        return redirect(url_for("survey.index"))

    return render_template(
        "survey/index.html",
        form=form,
        survey_processor=survey_processor,
        curr_testing_mode=curr_testing_mode(),
    )


@role_required(Role.Enumerator)
@survey_blueprint.route("/on-behalf-of/<respondent_uuid>")
def on_behalf_of(respondent_uuid: str):
    """
    Cache respondent UUID if enumerator conducts survey on their behalf.
    """
    if survey_session.respondent_uuid is None:
        survey_session.set_respondent_uuid(respondent_uuid)
        return redirect(url_for("survey.index"))
    elif survey_session.respondent_uuid == respondent_uuid:
        return redirect(url_for("survey.index"))
    else:
        # TODO: Flash message ("Survey in progress for another respondent")
        return redirect(url_for("enumerator.index"))


@survey_blueprint.route("/back")
def back():
    # Ensure full "refresh" by moving back twice and forward once
    survey_processor.back()
    if not survey_processor.curr_survey_start:
        survey_processor.back()
    survey_processor.next()

    return redirect(url_for("survey.index"))


@survey_blueprint.route("/submit")
def submit():
    if not survey_processor.curr_survey_end:
        return redirect(url_for("survey.index"))

    if curr_testing_mode():
        return redirect(url_for("index"))  # TODO: Flash message

    # Identify current respondent
    if current_user.role == Role.Respondent:
        respondent_uuid = current_user.uuid
    elif current_user.role == Role.Enumerator:
        respondent_uuid = survey_session.respondent_uuid
    else:
        # TODO: Flash message and redirect
        return f"Unknown role: {current_user.role}"

    # Garble survey response and store it into database
    survey_response = survey_processor.gather_survey_response()
    garbler.garble_and_store(survey_response, respondent_uuid)

    # Clear session data if response has been successfully stored in database
    survey_processor.clear_session()

    return "Survey response submitted"  # TODO: Flash message and redirect
