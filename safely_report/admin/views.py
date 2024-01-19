from flask import current_app, flash, redirect, session, url_for
from flask_admin import AdminIndexView, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_login import current_user
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import SelectField, SubmitField

from safely_report.models import Enumerator, Respondent, Role


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


class EnumeratorAssignmentForm(FlaskForm):
    field = SelectField("Select enumerator:", coerce=int)
    submit = SubmitField("Assign")


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

    @action("assign_enumerator", "Assign Enumerator")
    def action_assign_enumerator(self, ids):
        """
        Custom action to enable bulk-assigning respondents to an enumerator.

        Functioning more as an entry point, it delegates actual logic to
        a route for proper form handling.
        """
        session["respondent_ids_selected"] = ids
        return redirect(url_for("respondents.assign_enumerator"))

    @expose("/assign-enumerator", methods=["GET", "POST"])
    def assign_enumerator(self):
        """
        Route implementing logic to bulk-assign respondents to an enumerator.
        """
        # Construct form and choices for enumerator assignment
        form = EnumeratorAssignmentForm()
        form.field.choices = [(-99999, "")] + [
            (enumerator.id, str(enumerator))
            for enumerator in Enumerator.query.all()
        ]

        if form.validate_on_submit():
            # Identify the submitted enumerator
            enumerator_id = form.field.data
            enumerator = Enumerator.query.filter_by(id=enumerator_id).first()

            # Assign the enumerator to the selected respondents
            ids = session.get("respondent_ids_selected", [])
            respondents = Respondent.query.filter(Respondent.id.in_(ids)).all()
            for respondent in respondents:
                respondent.enumerator = enumerator

            # Commit changes to database
            try:
                self.session.commit()
                flash("Enumerator assigned successfully.", "success")
            except Exception as e:
                self.session.rollback()
                flash(f"Failed to assign enumerator. {str(e)}", "error")
            finally:
                session["respondent_ids_selected"] = None
                return redirect(url_for("respondents.index_view"))

        return self.render("admin/respondents/assign.html", form=form)


class EnumeratorModelView(SurveyModelView):
    pass
