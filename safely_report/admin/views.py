from flask import current_app, flash, redirect, request, url_for
from flask_admin import AdminIndexView, BaseView, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_login import current_user
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import SelectField, SubmitField

from safely_report.models import (
    Enumerator,
    GlobalState,
    Respondent,
    Role,
    SurveyResponse,
    SurveyStatus,
)
from safely_report.utils import make_download_response


class AdminView(BaseView):
    """
    Base class for all admin views.
    """

    # Restrict access to admin only
    def is_accessible(self):
        return getattr(current_user, "role", None) == Role.Admin

    # Handle unauthorized access
    def inaccessible_callback(self, name, **kwargs):
        return current_app.login_manager.unauthorized()


class SurveyAdminIndexView(AdminView, AdminIndexView):
    # Use custom template
    @expose("/")
    def index(self):
        return self.render("admin/custom_index.html")

    @expose("/switch-survey-activation")
    def switch_survey_activation(self):
        if GlobalState.is_survey_active():
            GlobalState.deactivate_survey()
            current_app.logger.info("Survey deactivated")
        else:
            GlobalState.activate_survey()
            current_app.logger.info("Survey reactivated")

        return redirect(url_for("admin.index"))


class SurveyModelView(AdminView, ModelView):
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
    list_template = "admin/respondents/list.html"

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
            message = (
                f"{str(model)} cannot be updated because "
                "they already completed survey."
            )
            flash(message, "error")
            return False
        return super().update_model(form, model)

    # Prevent deletion of respondent record once their response is submitted
    def delete_model(self, model):
        if model.survey_status == SurveyStatus.Complete:
            message = (
                f"{str(model)} cannot be deleted because "
                "they already completed survey."
            )
            flash(message, "error")
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
                    message = (
                        f"{str(respondent)} cannot be updated because "
                        "they already completed survey."
                    )
                    flash(message, "error")
                    continue  # Skip to next respondent
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

    @expose("/download")
    def download(self):
        current_app.logger.info("Downloading respondent roster")
        return make_download_response(
            content=Respondent.to_csv_string(),
            content_type="text/csv",
            file_name="respondents.csv",
        )


class EnumeratorModelView(SurveyModelView):
    list_template = "admin/enumerators/list.html"

    # Prevent deletion of enumerator record once they submit response
    # on behalf of their assigned respondent
    def delete_model(self, model):
        query = SurveyResponse.query.filter_by(enumerator_uuid=model.uuid)
        n_assisted = query.count()

        if n_assisted > 0:
            message = (
                f"{str(model)} cannot be deleted because "
                "they already assisted respondents."
            )
            flash(message, "error")
            return False

        return super().delete_model(model)

    @expose("/download")
    def download(self):
        current_app.logger.info("Downloading enumerator roster")
        return make_download_response(
            content=Enumerator.to_csv_string(),
            content_type="text/csv",
            file_name="enumerators.csv",
        )


class SubmissionView(AdminView):
    """
    A view for downloading submitted survey responses.
    """

    @expose("/")
    def index(self):
        count_total = Respondent.query.count()
        count_submitted = SurveyResponse.query.count()
        return self.render(
            "admin/submissions/index.html",
            count_total=count_total,
            count_submitted=count_submitted,
        )

    @expose("/download")
    def download(self):
        current_app.logger.info("Downloading submitted responses")
        return make_download_response(
            content=SurveyResponse.to_csv_string(),
            content_type="text/csv",
            file_name="submissions.csv",
        )
