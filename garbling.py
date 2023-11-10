from dataclasses import dataclass
from enum import Enum
from math import ceil
from random import random, shuffle
from typing import Any, Optional, Union

from pyxform.xls2json import parse_file_to_json


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
    path_to_xlsform: str
        Path to the XLSForm file specifying the survey

    Attributes
    ----------
    _params: dict[str, GarblingParams]
        Dictionary that maps garbling parameters onto
        the corresponding target question name
    """

    def __init__(self, path_to_xlsform: str):
        self._params = self._parse_xlsform(path_to_xlsform)

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

    @staticmethod
    def garble_individual_response(
        garbling_params: GarblingParams,
        response_value: str,
    ) -> tuple[str, int]:
        """
        Garble the given response at the individual level.

        Parameters
        ----------
        garbling_params: GarblingParams
            Garbling parameters
        response_value: str
            Name (not label) of the choice option that the respondent selected

        Returns
        -------
        str
            Name (not label) of the choice option after garbling is applied
        int:
            Count of cases where garbling has been applied
        """
        if garbling_params.scheme != GarblingScheme.IID:
            raise Exception("This method is valid only for IID Garbling")

        # Randomize garbling shock at the individual level
        garbling_shock = True if random() < garbling_params.rate else False

        # Perform garbling
        garbled_value = Garbler._garble_response(
            garbling_answer=garbling_params.answer,
            garbling_shock=garbling_shock,
            response_value=response_value,
        )

        return garbled_value, int(garbling_shock)

    @staticmethod
    def garble_block_responses(
        garbling_params: GarblingParams,
        response_values: list[Union[str, None]],
    ) -> tuple[list[Union[str, None]], int]:
        """
        Garble the given responses at the block level.

        Parameters
        ----------
        garbling_params: GarblingParams
            Garbling parameters
        response_values: list[Union[str, None]]
            Name (not label) of the choice option that each respondent selected

        Returns
        -------
        list[Union[str, None]]
            Names (not labels) of the choice options after garbling is applied
        int:
            Count of cases where garbling has been applied

        Notes
        -----
        - Note that this method performs Population-Blocked Garbling on the
        provided response values. Hence, for Covariate-Blocked Garbling, one
        should only pass in response values from the same covariate block; and
        repeat the process for different covariate blocks.
        - In a survey, some participants do not complete their responses, and
        such cases are captured by `None` values in `response_values`. We do
        not apply garbling in these cases.
        """
        block_schemes = [GarblingScheme.PopBlock, GarblingScheme.CovBlock]
        if garbling_params.scheme not in block_schemes:
            raise Exception("This method is valid only for Blocked Garbling")

        # Initialize the array of garbling shocks
        n = len(response_values)
        k = ceil(garbling_params.rate * n)  # To ensure we use integer
        garbling_shocks = [True] * k + [False] * (n - k)

        # Shuffle the array for randomization
        shuffle(garbling_shocks)

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
                    garbling_answer=garbling_params.answer,
                    garbling_shock=shock,
                    response_value=value,
                )
                garbled_response_values.append(garbled_value)

        return garbled_response_values, garbling_counter

    @staticmethod
    def _parse_xlsform(path_to_xlsform: str) -> dict[str, GarblingParams]:
        """
        Parse XLSForm to identify questions subject to garbling
        and their respective parameters.

        Parameters
        ----------
        path_to_xlsform: str
            Path to the XLSForm file specifying the survey

        Returns
        -------
        dict[str, GarblingParams]
            Dictionary that maps garbling parameters onto
            the corresponding target question name
        """
        survey_dict = parse_file_to_json(path=path_to_xlsform)

        # Initiate array to store survey elements subject to garbling
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
            garbling_params[name] = Garbler._extract_garbling_params(element)

        return garbling_params

    @staticmethod
    def _extract_garbling_params(
        survey_dict_record: dict[str, Any]
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
        rate = float(params.get("rate", 0))
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
