from flask_admin import Admin

from safely_report.admin.views import (
    EnumeratorModelView,
    RespondentModelView,
    SubmissionView,
    SurveyAdminIndexView,
)
from safely_report.models import Enumerator, Respondent, db

admin = Admin(
    name="Safely Report",
    index_view=SurveyAdminIndexView(),
    base_template="admin/custom_base.html",
)

admin.add_view(
    RespondentModelView(
        model=Respondent,
        session=db.session,
        name="Respondents",
        endpoint="respondents",
    )
)

admin.add_view(
    EnumeratorModelView(
        model=Enumerator,
        session=db.session,
        name="Enumerators",
        endpoint="enumerators",
    )
)

admin.add_view(
    SubmissionView(
        name="Submissions",
        endpoint="submissions",
    )
)
