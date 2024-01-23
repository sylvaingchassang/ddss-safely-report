from flask import Blueprint, redirect, render_template, session, url_for
from flask_login import current_user, login_required, logout_user

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


@survey_blueprint.before_request
@login_required
def require_auth():
    pass  # Actual implementation handled by decorator


@survey_blueprint.route("/", methods=["GET", "POST"])
def index():
    curr_testing_mode = current_user.role != Role.Respondent

    if survey_processor.curr_survey_end:
        return render_template(
            "survey/submit.html",
            curr_testing_mode=curr_testing_mode,
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
        curr_testing_mode=curr_testing_mode,
    )


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
    survey_processor.clear_data()

    # If real survey session, log out too
    if current_user.role == Role.Respondent:
        logout_user()

    return redirect(url_for("index"))


@survey_blueprint.route("/submit")
def submit():
    if not survey_processor.curr_survey_end:
        return redirect(url_for("survey.index"))

    if current_user.role != Role.Respondent:
        survey_processor.clear_data()
        return redirect(url_for("index"))  # TODO: Flash message

    # Garble survey response and store it into database
    garbler.garble_and_store(
        survey_response=survey_processor.gather_survey_response(),
        respondent_uuid=current_user.uuid,
        enumerator_uuid=session.get("enumerator_uuid"),
    )

    # Clear session data if response has been successfully stored in database
    session.clear()

    return "Survey response submitted"  # TODO: Flash message and redirect
