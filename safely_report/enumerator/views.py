from flask import Blueprint, render_template
from flask_login import current_user, login_required

from safely_report.auth.utils import role_required
from safely_report.models import Respondent, ResponseStatus, Role

enumerator_blueprint = Blueprint("enumerator", __name__)


@enumerator_blueprint.before_request
@login_required
@role_required(Role.Enumerator)
def require_auth():
    pass  # Actual implementation handled by decorator


@enumerator_blueprint.route("/")
def index():
    # List respondent attributes to display
    attributes = Respondent.__table__.columns.keys()
    attributes_to_hide = ["uuid", "enumerator_uuid", "id", "response_status"]
    attributes_to_show = [a for a in attributes if a not in attributes_to_hide]

    # Retrieve assigned respondent records
    respondents = (
        Respondent.query.filter_by(enumerator=current_user)
        .order_by(Respondent.response_status.desc())  # Incomplete first
        .all()
    )

    return render_template(
        "enumerator/index.html",
        attributes=attributes_to_show,
        respondents=respondents,
        incomplete_status=ResponseStatus.Incomplete,
    )
