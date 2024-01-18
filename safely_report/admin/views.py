from flask import current_app
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_login import current_user
from markupsafe import Markup

from safely_report.models import Role


class SurveyAdminIndexView(AdminIndexView):
    # Use custom template
    @expose("/")
    def index(self):
        return self.render("admin/index.html")

    # Restrict access to admin only
    def is_accessible(self):
        return getattr(current_user, "role", None) == Role.Admin

    # Handle unauthorized access
    def inaccessible_callback(self, name, **kwargs):
        return current_app.login_manager.unauthorized()


class SurveyModelView(ModelView):
    # Use custom list view template to enable UUID click-to-copy
    list_template = "admin/model/custom_list.html"

    # Enable CSRF protection
    form_base_class = SecureForm

    # Show primary keys in list view
    column_display_pk = True

    # Exclude UUID from create/edit view at all
    form_excluded_columns = ["uuid"]

    # Use informative display names for columns
    column_labels = {"id": "ID", "uuid": "UUID"}

    # Format UUIDs to enable click-to-copy
    column_formatters = {
        "uuid": lambda v, c, m, p: Markup(
            f'<button class="click-to-copy" title="Copy">{m.uuid}</button>'
        )
    }

    # Restrict access to admin only
    def is_accessible(self):
        return getattr(current_user, "role", None) == Role.Admin

    # Handle unauthorized access
    def inaccessible_callback(self, name, **kwargs):
        return current_app.login_manager.unauthorized()

    # Show UUID in the final column
    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        columns.remove("uuid")
        columns.append("uuid")
        return columns

    # Disable sorting for UUID
    def scaffold_sortable_columns(self):
        columns = super().scaffold_sortable_columns()
        columns.pop("uuid")
        return columns


class RespondentModelView(SurveyModelView):
    # Exclude survey status from create/edit view at all
    form_excluded_columns = [
        *SurveyModelView.form_excluded_columns,
        *["survey_status"],
    ]

    # Make assigned enumerator editable in list view
    column_editable_list = ["enumerator"]

    # Use informative display names for columns
    column_labels = {
        **SurveyModelView.column_labels,
        **{"enumerator": "Assigned Enumerator"},
    }

    # Show assigned enumerator and survey status in the final columns
    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        columns.remove("survey_status")
        columns.append("enumerator")
        columns.append("survey_status")
        return columns

    # Enable sorting for assigned enumerator
    def get_sortable_columns(self):
        columns = list(super().scaffold_sortable_columns().keys())
        columns.append(("enumerator", "enumerator.id"))
        self.column_sortable_list = columns
        return super().get_sortable_columns()


class EnumeratorModelView(SurveyModelView):
    pass
