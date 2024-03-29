from flask_login import current_user
from safely_report.models import Respondent, Role
from typing import Any


class XLSFormFunctions:
    """
    Implement Python counterparts (e.g., `_selected_at()`)
    of XLSForm functions (e.g., `selected-at()`).

    XLSForm functions are listed in the ODK documentation:
    https://docs.getodk.org/form-operators-functions/

    NOTE: These methods are to be inherited and used by
    `SurveyProcessor` to process XLSForm logic, so they need
    to follow consistent naming format (e.g., single leading
    underscore).
    """

    @classmethod
    def _if(cls, condition: bool, then: Any, otherwise: Any) -> Any:
        return then if condition is True else otherwise

    @classmethod
    def _selected(cls, choice_array: list[str], choice: str) -> bool:
        return choice in choice_array

    @classmethod
    def _selected_at(cls, choice_array: list[str], index: int) -> str:
        try:
            return choice_array[index]
        except IndexError:
            return ""

    @classmethod
    def _str_to_int(cls, value: str):
        return int(value)

    @classmethod
    def _pulldata(cls, column, default):
        """
        Assumes that all data is pulled from the respondent roster table

        Parameters
        ----------
        column: the field you want to retrieve
        default: a default value in case the field is not available, or the
            user is an Enumerator

        Returns
        -------
        field value if available, default otherwise
        """
        if current_user.role != Role.Respondent:
            return default

        respondent_uuid = current_user.uuid
        respondent = Respondent.query.filter_by(uuid=respondent_uuid).first()

        if hasattr(respondent, column):
            return getattr(respondent, column)
        else:
            return default
