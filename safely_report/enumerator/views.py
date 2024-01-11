from flask import Blueprint
from flask_login import current_user

from safely_report.models import Respondent

enum_blueprint = Blueprint("enum", __name__)


@enum_blueprint.route("/")
def index():
    respondents = Respondent.query.filter_by(enumerator=current_user).all()
    return [str(r) for r in respondents]
