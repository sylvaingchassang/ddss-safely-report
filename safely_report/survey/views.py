from flask import Blueprint, redirect, render_template, url_for

from safely_report import form_generator, garbler, survey_processor

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

    # Garble survey response and store it into database
    survey_response = survey_processor.gather_survey_response()
    garbler.garble_and_store(survey_response)

    # Clear session data if response has been successfully stored in database
    survey_processor.clear_session()

    return "Survey response submitted"
