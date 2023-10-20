from typing import Any


class Garbler:
    def __init__(self, survey_json: dict[str, Any]):
        self._params = self._parse_survey_json(survey_json)

    def _parse_survey_json(
        self, survey_json: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Parse the JSON representation of the survey produced by
        `pyxform.xls2json.parse_file_to_json()` to identify questions
        subject to garbling and their respective parameters.
        """
        # TODO: Raise error if garbling is specified to elements that
        # do NOT take user input

        # TODO: Raise error if not binary choice question

        # TODO: Raise error if target answer is not in choice options

        pass

    def is_subject_to_garbling(self, survey_element_name: str) -> bool:
        """
        Determine whether the given survey element is subject to garbling.
        """
        pass

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

        pass
