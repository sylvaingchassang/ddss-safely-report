from dataclasses import dataclass
from enum import Enum
from random import random, shuffle
from typing import Any, Optional

from flask_sqlalchemy import SQLAlchemy
from pyxform.xls2json import parse_file_to_json

from safely_report.models import GarblingBlock, SurveyResponse
from safely_report.survey.survey_session import SurveySession
from safely_report.utils import (
    check_dict_required_fields,
    deserialize,
    serialize,
)


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
    survey_session: SurveySession
        Session object for caching data specific to current survey respondent
    db: SQLAlchemy
        An instance of database connection
    """

    # To better support different block sizes in block garbling, we use
    # a mini-batch approach, where shocks are generated and used in small
    # batches that achieve the target garbling rate. For instance, garbling
    # one out of every two reports will eventually result in 50% garbling rate
    # (excluding the last "incomplete" batch that may exist if the block size
    # is not a multiple of the batch size). The following class attribute
    # defines shock batch for each supported rate in block garbling
    _block_garbling_shocks = {
        0.2: [True] * 1 + [False] * 4,
        0.25: [True] * 1 + [False] * 3,
        0.4: [True] * 2 + [False] * 3,
        0.5: [True] * 1 + [False] * 1,
        0.6: [True] * 3 + [False] * 2,
        0.75: [True] * 3 + [False] * 1,
        0.8: [True] * 4 + [False] * 1,
    }

    def __init__(
        self,
        path_to_xlsform: str,
        survey_session: SurveySession,
        db: SQLAlchemy,
    ):
        self._params = Garbler._parse_xlsform(path_to_xlsform)
        self._session = survey_session
        self._db = db

        # TODO: Cache covariate info of current survey respondent
        # (create and use related methods in SurveySession)
        pass

    def garble_and_store(self, survey_response: dict[str, Any]):
        try:
            # Apply garbling
            for varname, response_value in survey_response.items():
                garbling_params = self._params.get(varname)
                if garbling_params is None:
                    continue
                garbling_shock = self._get_garbling_shock(garbling_params)
                survey_response[varname] = Garbler._garble_response(
                    response_value=response_value,
                    garbling_shock=garbling_shock,
                    garbling_answer=garbling_params.answer,
                )

            # Serialize and store the garbled survey response
            response_serialized = serialize(survey_response)
            response_record = SurveyResponse(response=response_serialized)
            self._db.session.add(response_record)
            self._db.session.commit()
        except Exception as e:
            self._db.session.rollback()
            raise e

    def _get_garbling_shock(self, garbling_params: GarblingParams) -> bool:
        """
        Produce a random state for garbling a survey response according to
        the given parameters.

        Parameters
        ----------
        garbling_params: GarblingParams
            Garbling parameters of a survey element

        Returns
        -------
        bool
            Garbling "shock" that takes the value of either 1 (`True`)
            or 0 (`False`) with the given garbling probability
        """
        scheme = garbling_params.scheme

        if scheme == GarblingScheme.IID:
            # Randomize garbling shock at the individual level
            garbling_shock = True if random() < garbling_params.rate else False
        elif scheme in [GarblingScheme.PopBlock, GarblingScheme.CovBlock]:
            block_name = garbling_params.question
            if garbling_params.covariate:
                # TODO: Update block_name to be a combination of the question
                # name and the respondent's covariate value (e.g., married)
                pass

            # Get the garbling block info
            block = GarblingBlock.query.filter_by(name=block_name).first()
            if block is None:
                block = GarblingBlock(name=block_name, shocks=serialize([]))
            if len(deserialize(block.shocks)) == 0:
                shocks = Garbler._block_garbling_shocks[garbling_params.rate]
                shuffle(shocks)
                block.shocks = serialize(shocks)

            # Randomize garbling shock at the block level
            shocks = deserialize(block.shocks)
            garbling_shock = shocks.pop()
            block.shocks = serialize(shocks)

            # Register changes in the garbling block info
            self._db.session.add(block)  # To be committed later
        else:
            raise Exception(f"Unsupported garbling scheme: {scheme}")

        return garbling_shock

    @staticmethod
    def _garble_response(
        response_value: str, garbling_shock: bool, garbling_answer: str
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
        response_value: str
            Name (not label) of the choice option that the respondent selected
        garbling_shock: bool
            Garbling "shock" that takes the value of either 1 (`True`)
            or 0 (`False`) with the given garbling probability
        garbling_answer: str
            Name (not label) of the choice option to be garbled *into*
            (most of the time, it is the name of the "yes" choice option)

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

        # Recursively identify survey elements subject to garbling
        # NOTE: Ensure no garbling happens inside any repeat section
        a = Garbler._find_elements_with_garbling(survey_dict)
        b = Garbler._find_elements_with_garbling(survey_dict, skip_repeat=True)
        if len(a) > len(b):
            raise Exception("Garbling should not be applied inside repeats")
        elements_with_garbling = b

        # Extract and organize garbling parameters
        garbling_params = {}
        for element in elements_with_garbling:
            name = element.get("name", "")
            garbling_params[name] = Garbler._extract_garbling_params(element)

        return garbling_params

    @staticmethod
    def _find_elements_with_garbling(
        element: dict[str, Any],
        skip_repeat: bool = False,
        elements_with_garbling: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """
        Recursively identify survey elements subject to garbling.

        Parameters
        ----------
        element: dict[str, Any]
            A record in the dictionary representation of the survey
            produced by `pyxform.xls2json.parse_file_to_json()`
        skip_repeat: bool
            Whether to discard survey elements under repeat sections
        elements_with_garbling: list[dict[str, Any]], optional
            Existing array of survey elements subject to garbling

        Returns
        -------
        list[dict[str, Any]]
            Array of survey elements subject to garbling
        """
        if elements_with_garbling is None:
            elements_with_garbling = []

        # Determine whether the given survey element is a repeat section
        is_repeat = element.get("type") == "repeat"

        # Recursively identify survey elements subject to garbling
        if not skip_repeat or (skip_repeat and not is_repeat):
            if element.get("garbling"):
                elements_with_garbling.append(element)
            if element.get("children"):
                for child in element["children"]:
                    Garbler._find_elements_with_garbling(
                        element=child,
                        skip_repeat=skip_repeat,
                        elements_with_garbling=elements_with_garbling,
                    )

        return elements_with_garbling

    @staticmethod
    def _extract_garbling_params(element: dict[str, Any]) -> GarblingParams:
        """
        Extract, validate, and repackage garbling parameters
        for the given survey element record.

        Parameters
        ----------
        element: dict[str, Any]
            A record in the dictionary representation of the survey
            produced by `pyxform.xls2json.parse_file_to_json()`

        Returns
        -------
        GarblingParams
            Streamlined packaging of validated garbling parameters
        """
        # Unpack the given survey record
        check_dict_required_fields(
            data=element,
            required_fields=[
                ("name", str),
                ("choices", list),
                ("garbling", dict),
            ],
        )
        params = element["garbling"]
        question = element["name"]
        choices = element["choices"]

        # Unpack garbling parameters
        check_dict_required_fields(
            data=params,
            required_fields=[("answer", str), ("rate", str)],
        )
        answer = params["answer"]
        rate = float(params["rate"])
        covariate = params.get("covariate")  # Optional param

        # Validate garbling parameters
        if len(choices) != 2:
            raise Exception(
                "Garbling specified for a non binary-choice question: "
                f"{question}"
            )
        choice_names = [c.get("name", "") for c in choices]
        if answer not in choice_names:
            raise Exception(f"{answer} not in choice options for {question}")
        if rate < 0 or rate > 1:
            raise ValueError("Garbling rate should be between 0 and 1")
        if covariate and (rate not in Garbler._block_garbling_shocks):
            raise ValueError(
                "Block garbling supports the following rates only: "
                f"{list(Garbler._block_garbling_shocks.keys())}"
            )

        return GarblingParams(question, answer, rate, covariate)
