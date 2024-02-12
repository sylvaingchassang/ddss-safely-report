from typing import Any


class SurveyProcessorBase:
    """
    Base class defining survey processor's custom methods
    (e.g., `_selected_at()`) to replace XLSForm functions
    (e.g., `selected-at()`).

    Functions to replace are listed in the ODK documentation:
    https://docs.getodk.org/form-operators-functions/

    NOTE: This base class only defines static methods that do not
    reference or alter internal states of the survey processor.
    Methods that need access to the survey processor's states
    should be defined in the child class (i.e., `SurveyProcessor`)
    where state variables and their behaviors are defined.
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
