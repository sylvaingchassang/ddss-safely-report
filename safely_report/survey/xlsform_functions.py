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
