from typing import Any, Callable, Optional

from flask_wtf import FlaskForm
from wtforms import (
    Field,
    RadioField,
    SelectMultipleField,
    StringField,
    SubmitField,
    widgets,
)
from wtforms.validators import ValidationError

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

    def _make_curr_field(self) -> Field:
        # Identify current survey element type
        curr_type = self._processor.curr_type

        # Collect function arguments common to all field types
        common_args = {
            "label": self._curr_label,
            "validators": self._curr_validators,
            "default": self._curr_default,
        }

        if curr_type == "text":
            return StringField(**common_args)
        elif curr_type == "select one":
            return RadioField(**common_args, choices=self._curr_choices)
        elif curr_type == "select all that apply":
            return SelectMultipleField(
                **common_args,
                choices=self._curr_choices,
                widget=widgets.ListWidget(prefix_label=False),
                option_widget=widgets.CheckboxInput()
            )

    @property
    def _curr_label(self) -> str:
        return self._processor.curr_label

    @property
    def _curr_validators(self) -> list[Callable]:
        # Define validator for the constraint of the current survey element
        def evaluate_constraint(form: FlaskForm, field: Field):
            value = field.data
            if self._processor.set_curr_value(value) is False:
                # TODO: Provide a more detailed error message
                raise ValidationError("Value constraint violated")

        # Define validator for required response
        def data_required(form: FlaskForm, field: Field):
            if not field.data:
                raise ValidationError("Response is required for this question")

        # Collect validators to use
        validators = [evaluate_constraint]
        if self._processor.curr_required is True:
            validators.append(data_required)

        return validators

    @property
    def _curr_default(self) -> Optional[Any]:
        # Pre-fill the field if prior response exists
        try:
            default = self._processor.curr_value
        except KeyError:
            default = None

        return default

    @property
    def _curr_choices(self) -> Optional[list[tuple[str, str]]]:
        return self._processor.curr_choices
