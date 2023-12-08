from flask import Blueprint, redirect, render_template, url_for

from safely_report import db, form_generator, survey_processor
from safely_report.models import SurveyResponse
from safely_report.utils import serialize

survey_blueprint = Blueprint(
    "survey", __name__, template_folder="templates/survey"
)


@survey_blueprint.route("/", methods=["GET", "POST"])
def index():
    if survey_processor.curr_survey_end:
        return render_template("submit_survey.html")

    if survey_processor.curr_survey_start:
        survey_processor.next()  # Roll forward to first displayable element

    form = form_generator.make_curr_form()

    if form.validate_on_submit():
        survey_processor.next()
        return redirect(url_for("survey.index"))

    return render_template(
        "run_survey.html",
        form=form,
        survey_processor=survey_processor,
    )


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

    # Store survey response into database
    try:
        response_dict = survey_processor.gather_survey_response()
        response_serialized = serialize(response_dict)
        response_record = SurveyResponse(response=response_serialized)
        db.session.add(response_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return e

    # Clear session data if response has been successfully stored in database
    survey_processor.clear_session()

    return "Survey response submitted"
