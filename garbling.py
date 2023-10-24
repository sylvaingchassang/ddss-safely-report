from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class GarblingScheme(Enum):
    IID = "Independent and Identically Distributed"
    PopBlock = "Population-Blocked"
    CovBlock = "Covariate-Blocked"


@dataclass(frozen=True)
class GarblingParams:
    # Name of the survey element to be garbled
    question: str

    # Name (not label) of the choice option to be garbled *into*
    # Most of the time, it is the name of the "yes" choice option
    answer: str

    # Garbling probability
    rate: float

    # Name of a covariate to use for Covariate-Blocked Garbling
    covariate: Optional[str]

    @property
    def scheme(self) -> GarblingScheme:
        if not self.covariate:
            return GarblingScheme.IID
        elif self.covariate == "*":
            return GarblingScheme.PopBlock
        else:
            return GarblingScheme.CovBlock


class Garbler:
    """
    A garbling engine that parses garbling specifications in XLSForm
    and uses them to perform different garbling schemes.

    Parameters
    ----------
    survey_dict: dict[str, Any]
        Dictionary representation of the survey produced by
        `pyxform.xls2json.parse_file_to_json()`

    Attributes
    ----------
    _params: dict[str, GarblingParams]
        Dictionary that maps garbling parameters onto
        the corresponding target question name
    """

    def __init__(self, survey_dict: dict[str, Any]):
        self._params = self._parse_survey_dict(survey_dict)

    def _parse_survey_dict(
        self, survey_dict: dict[str, Any]
    ) -> dict[str, GarblingParams]:
        """
        Parse dictionary representation of the survey produced by
        `pyxform.xls2json.parse_file_to_json()` to identify questions
        subject to garbling and their respective parameters.
        """
        elements_with_garbling = []

        def find_elements_with_garbling(element):
            if element.get("garbling"):
                elements_with_garbling.append(element)
            if element.get("children"):
                for child in element["children"]:
                    find_elements_with_garbling(child)

        # Recursively identify survey elements subject to garbling
        find_elements_with_garbling(survey_dict)

        # Extract and organize garbling parameters
        garbling_params = {}
        for element in elements_with_garbling:
            name = element.get("name", "")
            garbling_params[name] = self._extract_garbling_params(element)

        return garbling_params

    def _extract_garbling_params(
        self, survey_element_record: dict[str, Any]
    ) -> GarblingParams:
        """
        Extract, validate, and repackage garbling parameters
        for the given survey element record.
        """
        # Unpack garbling parameters
        params = survey_element_record.get("garbling", {})
        question = survey_element_record.get("name", "")
        answer = params.get("answer", "")
        rate = params.get("rate", 0)
        covariate = params.get("covariate", "")

        # Validate garbling parameters
        name = survey_element_record.get("name", "")
        choices = survey_element_record.get("choices", [])
        if len(choices) != 2:
            raise Exception(
                f"Garbling specified for a non binary-choice question: {name}"
            )
        choice_names = [c.get("name", "") for c in choices]
        if answer not in choice_names:
            raise Exception(f"{answer} not in choice options for {name}")

        return GarblingParams(question, answer, rate, covariate)

    def find_whether_to_garble(self, survey_element_name: str) -> bool:
        """
        Determine whether the given survey element is subject to garbling.
        """
        if self._params.get(survey_element_name):
            return True
        return False

    def garble_response(
        self, survey_element_name: str, choice_name: str
    ) -> str:
        """
        Using the given element's garbling parameters,
        apply garbling formula to garble the given response.
        """
        # TODO: Raise error if the given survey element is NOT subject to
        # garbling

        # TODO: If the response has actually been flipped/switched, increment
        # garbling counter (cached in server-side session; stored into DB's
        # counter table once the current survey session is submitted; counter
        # table has each respondent's counter record as a separate record and
        # these records will be "summed up" when the counter data is downloaded
        # after survey deactivation)
        # NOTE: Perhaps this should be done in SurveyProcessor as it has direct
        # interaction with SurveySession

        pass
