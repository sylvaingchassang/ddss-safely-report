from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm


class SurveyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        return self.render("admin/index.html")


class SurveyModelView(ModelView):
    form_base_class = SecureForm
    column_display_pk = True
    column_labels = {"uuid": "UUID"}

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
    column_display_all_relations = True
    column_editable_list = ["enumerator"]

    # Show assigned enumerator in the final column
    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        columns.append("enumerator")
        return columns


class EnumeratorModelView(SurveyModelView):
    pass
