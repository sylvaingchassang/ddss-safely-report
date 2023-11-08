from dataclasses import dataclass
from enum import Enum
from math import ceil
from random import random, shuffle
from typing import Any, Optional, Union


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

    def get_garbling_params(
        self, survey_element_name: str
    ) -> Optional[GarblingParams]:
        """
        Retrieve garbling parameters of the given survey element.
        Return `None` if the given survey element is not subject to garbling.

        Parameters
        ----------
        survey_element_name: str
            Name of the survey element to be garbled

        Returns
        -------
        GarblingParams, optional
            Garbling parameters of the given survey element
        """
        return self._params.get(survey_element_name)

    def garble_responses(
        self,
        garbling_params: GarblingParams,
        response_values: list[Union[str, None]],
        covariate_values: Optional[list[str]] = [],
    ) -> tuple[list[Union[str, None]], int]:
        """
        Garble responses to the given survey element.

        Parameters
        ----------
        garbling_params: GarblingParams
            Garbling parameters
        response_values: list[Union[str, None]]
            Name (not label) of the choice option that each respondent selected
        covariate_values: list[str], optional
            Covariate value (e.g., "married") for each respondent

        Returns
        -------
        list[Union[str, None]]
            Names (not labels) of the choice options after garbling is applied
        int:
            Count of cases where garbling has been applied

        Notes
        -----
        - In a survey, some participants do not complete their responses, and
        such cases are captured by `None` values in `response_values`. We do
        not apply garbling in these cases.
        - Covariate information is part of the survey respondent roster, so
        `covariate_values` cannot contain any `None` values.
        """
        # Generate garbling shocks (i.e., `eta`s in the garbling formula)
        if garbling_params.scheme == GarblingScheme.IID:
            garbling_shocks = Garbler._generate_garbling_shocks_per_individual(
                rate=GarblingParams.rate, n=len(response_values)
            )
        elif garbling_params.scheme == GarblingScheme.PopBlock:
            garbling_shocks = Garbler._generate_garbling_shocks_per_block(
                rate=GarblingParams.rate, n=len(response_values)
            )
        elif garbling_params.scheme == GarblingScheme.CovBlock:
            pass
        else:
            raise Exception(f"{garbling_params.scheme} is not supported")

        # Perform garbling
        garbled_response_values: list[Union[str, None]] = []
        garbling_counter = 0
        for value, shock in zip(response_values, garbling_shocks):
            if value is None:
                garbled_response_values.append(None)
            else:
                if shock is True:
                    garbling_counter += 1
                garbled_value = Garbler._garble_response(
                    garbling_answer=GarblingParams.answer,
                    garbling_shock=shock,
                    response_value=value,
                )
                garbled_response_values.append(garbled_value)

        return garbled_response_values, garbling_counter

    def _parse_survey_dict(
        self, survey_dict: dict[str, Any]
    ) -> dict[str, GarblingParams]:
        """
        Parse dictionary representation of the survey produced by
        `pyxform.xls2json.parse_file_to_json()` to identify questions
        subject to garbling and their respective parameters.

        Parameters
        ----------
        survey_dict: dict[str, Any]
            Dictionary representation of the survey produced by
            `pyxform.xls2json.parse_file_to_json()`

        Returns
        -------
        dict[str, GarblingParams]
            Dictionary that maps garbling parameters onto
            the corresponding target question name
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
        self, survey_dict_record: dict[str, Any]
    ) -> GarblingParams:
        """
        Extract, validate, and repackage garbling parameters
        for the given survey element record.

        Parameters
        ----------
        survey_dict_record: dict[str, Any]
            A record in the dictionary representation of the survey
            produced by `pyxform.xls2json.parse_file_to_json()`

        Returns
        -------
        GarblingParams
            Streamlined packaging of validated garbling parameters
        """
        # Unpack garbling parameters
        params = survey_dict_record.get("garbling", {})
        question = survey_dict_record.get("name", "")
        answer = params.get("answer", "")
        rate = params.get("rate", 0)
        covariate = params.get("covariate", "")

        # Validate garbling parameters
        choices = survey_dict_record.get("choices", [])
        if len(choices) != 2:
            raise Exception(
                "Garbling specified for a non binary-choice question: "
                f"{question}"
            )
        choice_names = [c.get("name", "") for c in choices]
        if answer not in choice_names:
            raise Exception(f"{answer} not in choice options for {question}")
        if rate < 0 or rate > 1:
            raise Exception("Garbling rate should be between 0 and 1")

        return GarblingParams(question, answer, rate, covariate)

    @staticmethod
    def _generate_garbling_shocks_per_individual(
        rate: float, n: int
    ) -> list[bool]:
        """
        Randomize garbling shocks (i.e., `eta`s in the garbling formula)
        at the individual level.

        Parameters
        ----------
        rate: float
            Garbling probability
        n: int
            Number of garbling shocks to generate

        Returns
        -------
        list[bool]
            Array of garbling shocks generated
        """
        garbling_shocks = []
        for _ in range(n):
            shock = True if random() < rate else False
            garbling_shocks.append(shock)

        return garbling_shocks

    @staticmethod
    def _generate_garbling_shocks_per_block(rate: float, n: int) -> list[bool]:
        """
        Randomize garbling shocks (i.e., `eta`s in the garbling formula)
        at the block level.

        Parameters
        ----------
        rate: float
            Garbling probability
        n: int
            Number of garbling shocks to generate

        Returns
        -------
        list[bool]
            Array of garbling shocks generated
        """
        # Initialize the array of garbling shocks
        k = ceil(rate * n)  # To ensure we use integer
        garbling_shocks = [True] * k + [False] * (n - k)

        # Shuffle the array for randomization
        shuffle(garbling_shocks)

        return garbling_shocks

    @staticmethod
    def _garble_response(
        garbling_answer: str,
        garbling_shock: bool,
        response_value: str,
    ) -> str:
        """
        Apply garbling formula to the given response.

        With binary response between 0 and 1, garbling is formally defined as:

            r_tilde = r + (1 - r) * eta

        where:

            - `r` is the original raw response value
            - `eta` is a garbling "shock" that takes the value of either 1 or 0
            with the given garbling probability
            - `r_tilde` is the garbled response value

        For more details, consult the original paper:

            https://www.nber.org/papers/w31011

        Parameters
        ----------
        garbling_answer: str
            Name (not label) of the choice option to be garbled *into*
            (most of the time, it is the name of the "yes" choice option)
        garbling_shock: bool
            Garbling "shock" that takes the value of either 1 or 0
            with the given garbling probability
        response_value: str
            Name (not label) of the choice option that the respondent selected

        Returns
        -------
        str
            Name (not label) of the choice option after garbling is applied
        """
        if response_value == garbling_answer:
            return response_value
        else:
            if garbling_shock is True:
                return garbling_answer
            else:
                return response_value
