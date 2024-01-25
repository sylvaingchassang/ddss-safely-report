from flask import current_app, flash, make_response, redirect, request, url_for
from flask_admin import AdminIndexView, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_login import current_user
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import SelectField, SubmitField

from safely_report.admin.utils import gather_all_responses_to_csv
from safely_report.models import Enumerator, Respondent, Role, SurveyStatus


class SurveyAdminIndexView(AdminIndexView):
    # Restrict access to admin only
    def is_accessible(self):
        return getattr(current_user, "role", None) == Role.Admin

    # Handle unauthorized access
    def inaccessible_callback(self, name, **kwargs):
        return current_app.login_manager.unauthorized()

    # Use custom template
    @expose("/")
    def index(self):
        return self.render("admin/custom_index.html")

    # Route for exporting the (garbled) survey responses
    @expose("/export-responses")
    def export_responses(self):
        csv_string = gather_all_responses_to_csv()
        if csv_string == "":
            flash("No response exists yet", "error")
            return redirect(url_for("admin.index"))

        response = make_response(csv_string)
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = (
            "attachment; " "filename=responses.csv"
        )

        return response


class SurveyModelView(ModelView):
    """
    Define common setup for respondent and enumerator views.
    """

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

    # Enable column filters
    def get_filters(self):
        columns = super().scaffold_list_columns()
        self.column_filters = columns
        return super().get_filters()


class EnumeratorAssignmentForm(FlaskForm):
    """
    Form to be used for bulk-assigning respondents to an enumerator.
    """

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

    # Prevent changes to respondent info once their response is submitted
    def update_model(self, form, model):
        if model.survey_status == SurveyStatus.Complete:
            flash("Completed respondent cannot be edited.", "error")
            return False
        return super().update_model(form, model)

    # Prevent removal of respondent info once their response is submitted
    def delete_model(self, model):
        if model.survey_status == SurveyStatus.Complete:
            flash("Completed respondent cannot be deleted.", "error")
            return False
        return super().delete_model(model)

    @action("assign_enumerator", "Assign Enumerator")
    def action_assign_enumerator(self, ids):
        """
        Custom action to enable bulk-assigning respondents to an enumerator.

        Functioning more as an entry point, it delegates actual logic to
        a route for proper form handling.
        """
        # Pass along selected respondent IDs as a query parameter
        ids_str = ",".join(map(str, ids))
        return redirect(url_for("respondents.assign_enumerator", ids=ids_str))

    @expose("/assign-enumerator", methods=["GET", "POST"])
    def assign_enumerator(self):
        """
        Route implementing logic to bulk-assign respondents to an enumerator.
        """
        # Get respondent IDs from the query parameters
        ids_str = request.args.get("ids", "")
        ids = [int(id) for id in ids_str.split(",") if id]

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
            respondents = Respondent.query.filter(Respondent.id.in_(ids)).all()
            count = 0
            for respondent in respondents:
                if respondent.survey_status == SurveyStatus.Complete:
                    flash("Completed respondent cannot be edited.", "error")
                    continue
                respondent.enumerator = enumerator
                count += 1

            # Commit changes to database
            try:
                self.session.commit()
                flash(f"{count} records were successfully updated.", "success")
            except Exception as e:
                self.session.rollback()
                flash(f"Failed to update records. {str(e)}", "error")
            finally:
                return redirect(url_for("respondents.index_view"))

        return self.render("admin/respondents/assign.html", form=form)


class EnumeratorModelView(SurveyModelView):
    pass
