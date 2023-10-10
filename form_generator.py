from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError

from survey_processor import SurveyProcessor


class SurveyFormGenerator:
    """
    Generate a WTForms form for the survey processor's current element,
    which can be used by the front end to render the element.
    """

    def __init__(self, survey_processor: SurveyProcessor):
        self._processor = survey_processor

    def make_curr_form(self) -> FlaskForm:
        class SurveyElementForm(FlaskForm):
            field = self._make_curr_field()
            submit = SubmitField("Next")

        return SurveyElementForm()

    def _make_curr_field(self):
        # Define validator for the constraint of the current survey element
        def evaluate_constraint(form, field):
            value = field.data
            if self._processor.set_curr_value(value) is False:
                # TODO: Provide a more detailed error message
                raise ValidationError("Value constraint violated")

        # Collect validators to use
        validators = [evaluate_constraint]
        if self._processor.curr_required is True:
            validators.append(DataRequired())

        try:
            default = self._processor.curr_value
        except KeyError:
            default = None

        return StringField(
            label=self._processor.curr_label,
            validators=validators,
            default=default,
        )
