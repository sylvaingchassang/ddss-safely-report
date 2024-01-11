from flask import Blueprint, render_template
from flask_login import current_user, login_required

from safely_report.models import Respondent, Role

enumerator_blueprint = Blueprint("enumerator", __name__)


@enumerator_blueprint.before_request
@login_required
def require_enumerator():
    if current_user.role != Role.Enumerator:
        return "Unauthorized"  # TODO: Flash message and redirect


@enumerator_blueprint.route("/")
def index():
    # List respondent attributes to display
    attributes = Respondent.__table__.columns.keys()
    attributes_to_hide = ["uuid", "enumerator_uuid", "id"]
    attributes_to_show = [a for a in attributes if a not in attributes_to_hide]

    # Retrieve assigned respondent records
    respondents = Respondent.query.filter_by(enumerator=current_user).all()

    return render_template(
        "enumerator/index.html",
        attributes=attributes_to_show,
        respondents=respondents,
    )
