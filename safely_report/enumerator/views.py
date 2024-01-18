from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user

from safely_report.auth.utils import role_required
from safely_report.models import Respondent, Role, SurveyStatus, User

enumerator_blueprint = Blueprint("enumerator", __name__)


@enumerator_blueprint.before_request
@login_required
@role_required(Role.Enumerator)
def require_auth():
    pass  # Actual implementation handled by decorator


@enumerator_blueprint.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        respondent_uuid = request.form.get("respondent_uuid")
        enumerator_uuid = current_user.uuid

        # Access the survey on behalf of the respondent
        user = User.query.filter_by(uuid=respondent_uuid).first()
        if user is not None and user.role == Role.Respondent:
            session.clear()
            session["enumerator_uuid"] = enumerator_uuid
            login_user(user)
            return redirect(url_for("survey.index"))
        return "Respondent not found"  # TODO: Flash message and redirect

    # List respondent attributes to display
    attributes = Respondent.__table__.columns.keys()
    attributes_to_hide = ["uuid", "enumerator_uuid", "id", "survey_status"]
    attributes_to_show = [a for a in attributes if a not in attributes_to_hide]

    # Retrieve assigned respondent records
    respondents = (
        Respondent.query.filter_by(enumerator=current_user)
        .order_by(Respondent.survey_status.desc())  # Incomplete first
        .all()
    )

    return render_template(
        "enumerator/index.html",
        attributes=attributes_to_show,
        respondents=respondents,
        incomplete_status=SurveyStatus.Incomplete,
    )
