from flask import current_app
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_login import current_user

from safely_report.models import Role


class SurveyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        return self.render("admin/index.html")

    def is_accessible(self):
        return getattr(current_user, "role", None) == Role.Admin

    def inaccessible_callback(self, name, **kwargs):
        return current_app.login_manager.unauthorized()


class SurveyModelView(ModelView):
    form_base_class = SecureForm
    column_display_pk = True

    def is_accessible(self):
        return getattr(current_user, "role", None) == Role.Admin

    def inaccessible_callback(self, name, **kwargs):
        return current_app.login_manager.unauthorized()


class RespondentModelView(SurveyModelView):
    column_display_all_relations = True
    column_editable_list = ["enumerator"]
    column_labels = {"uuid": "UUID", "enumerator": "Assigned Enumerator"}
    form_widget_args = {"uuid": {"readonly": True}}

    # Show UUID and assigned enumerator in the final columns
    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        columns.remove("uuid")
        columns.append("uuid")
        columns.append("enumerator")
        return columns

    # Disable sorting for UUID; enable sorting for assigned enumerator
    def get_sortable_columns(self):
        columns = super().scaffold_list_columns()
        columns.remove("uuid")
        columns.append(("enumerator", "enumerator.id"))
        self.column_sortable_list = columns
        return super().get_sortable_columns()


class EnumeratorModelView(SurveyModelView):
    column_labels = {"uuid": "UUID"}
    form_widget_args = {"uuid": {"readonly": True}}

    # Show UUID in the final column
    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        columns.remove("uuid")
        columns.append("uuid")
        return columns

    # Disable sorting for UUID
    def get_sortable_columns(self):
        columns = super().scaffold_list_columns()
        columns.remove("uuid")
        self.column_sortable_list = columns
        return super().get_sortable_columns()
