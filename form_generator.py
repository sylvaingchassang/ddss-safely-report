from typing import Any, Callable, Optional

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DateTimeField,
    DecimalField,
    Field,
    IntegerField,
    RadioField,
    SelectMultipleField,
    StringField,
    SubmitField,
    widgets,
)
from wtforms.validators import StopValidation, ValidationError

from survey_processor import SurveyProcessor


class SurveyFormGenerator:
    """
    Generate a WTForms form for the survey processor's current element,
    which can be used by the front end to render the element.

    Parameters
    ----------
    survey_processor: SurveyProcessor
        An instance of the survey processing engine
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
            "description": self._curr_hint,
            "validators": self._curr_validators,
            "default": self._curr_default,
        }

        if curr_type == "note":
            return Field(**common_args)
        elif curr_type == "text":
            return StringField(**common_args)
        elif curr_type == "integer":
            return IntegerField(**common_args)
        elif curr_type == "decimal":
            return DecimalField(**common_args)
        elif curr_type == "date":
            return DateField(**common_args)
        elif curr_type == "datetime":
            return DateTimeField(**common_args)
        elif curr_type == "select one":
            return RadioField(**common_args, choices=self._curr_choices)
        elif curr_type == "select all that apply":
            return SelectMultipleField(
                **common_args,
                choices=self._curr_choices,
                widget=widgets.ListWidget(prefix_label=False),
                option_widget=widgets.CheckboxInput(),
            )

    @property
    def _curr_label(self) -> str:
        return self._processor.curr_label

    @property
    def _curr_hint(self) -> str:
        return self._processor.curr_hint

    @property
    def _curr_validators(self) -> list[Callable]:
        # Define validator to ensure a response is given to any
        # survey element designated as "required"
        # NOTE: This should come before any other validation
        def data_required(form: FlaskForm, field: Field):
            if self._processor.curr_required is True:
                if field.raw_data and field.raw_data[0]:
                    return
                field.errors[:] = []
                raise StopValidation("Response is required for this question")

        # Define validator to evaluate if the given response meets
        # the current survey element's constraint if any
        def constraint_met(form: FlaskForm, field: Field):
            value = field.data
            if self._processor.set_curr_value(value) is False:
                message = self._processor.curr_constraint_message
                if message:
                    raise ValidationError(message)
                else:
                    raise ValidationError("Value constraint violated")

        # Collect validators to use
        validators = [data_required, constraint_met]

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
