from flask import Blueprint, redirect, render_template, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from safely_report.auth.utils import role_required
from safely_report.models import GlobalState, Respondent, Role, User, db
from safely_report.settings import XLSFORM_PATH
from safely_report.survey.form_generator import SurveyFormGenerator
from safely_report.survey.garbling import Garbler
from safely_report.survey.survey_processor import SurveyProcessor

# Instantiate classes for conducting the survey
survey_processor = SurveyProcessor(XLSFORM_PATH, session)
garbler = Garbler(XLSFORM_PATH, db)
form_generator = SurveyFormGenerator(survey_processor)


survey_blueprint = Blueprint("survey", __name__)


@survey_blueprint.before_request
@login_required
def handle_deactivation():
    if not GlobalState.is_survey_active():
        if current_user.role == Role.Respondent:
            # TODO: Flash message and redirect
            return "Survey is currently disabled"


@survey_blueprint.context_processor
def inject_template_variables():
    return {"is_testing_mode": current_user.role != Role.Respondent}


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

    # Extract data necessary for displaying garbling information
    garbling_params = garbler.params.get(survey_processor.curr_name)
    curr_choices = survey_processor.curr_choices  # For garbling answer label

    return render_template(
        "survey/index.html",
        form=form,
        survey_processor=survey_processor,
        garbling_params=garbling_params,
        curr_choices=curr_choices,
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
        enumerator_uuid=survey_processor.enumerator_uuid,
    )

    # Log out and clear all session data
    logout_user()
    session.clear()

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
                logout_user()
                session.clear()
                login_user(user)
                survey_processor.set_enumerator_uuid(enumerator_uuid)
                return redirect(url_for("survey.index"))

    return "Respondent not found"  # TODO: Flash message and redirect
