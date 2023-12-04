from copy import deepcopy
from typing import Any, Optional

from flask.sessions import SessionMixin


class SurveySession:
    """
    An interface to limit and structure interaction with the (server-side)
    session object.

    NOTE: Flask session object cannot be modified outside of request context,
    which means session fields cannot be initiated before the app is running.
    To resolve this, we embed field initiation logic inside retrieval methods,
    i.e., we initiate the field if it does not exist.

    Parameters
    ----------
    session: SessionMixin
        Flask session object for caching data
    """

    # Define field names for storing user state info
    LANGUAGE = "survey_language"
    ELEMENT_VISITS = "survey_elements_visited"
    ELEMENT_VALUES = "survey_response_values"

    def __init__(self, session: SessionMixin):
        self._session = session

    @property
    def language(self) -> str:
        lang = self._session.get(SurveySession.LANGUAGE)
        if lang is None:
            self._session[SurveySession.LANGUAGE] = lang = ""
        return lang

    @property
    def latest_visit(self) -> Optional[str]:
        if len(self._visit_history) > 0:
            return self._visit_history[-1]
        return None

    def set_language(self, language_name: str):
        self._session[SurveySession.LANGUAGE] = language_name

    def add_new_visit(self, survey_element_name: str):
        self._visit_history.append(survey_element_name)
        self._session.modified = True

    def drop_latest_visit(self):
        if len(self._visit_history) > 0:
            self._visit_history.pop()
            self._session.modified = True

    def count_visits(self, survey_element_name: str) -> int:
        """
        Count the number of times that the given survey element has been
        visited so far.
        """
        return self._visit_history.count(survey_element_name)

    def get_all_visits(self) -> list[str]:
        return deepcopy(self._visit_history)

    def store_response(self, survey_element_name: str, response_value: Any):
        if response_value is None:
            self._response_values.pop(survey_element_name, None)
        else:
            self._response_values[survey_element_name] = response_value

        self._session.modified = True

    def retrieve_response(
        self, survey_element_name: str, default_value: Optional[Any] = None
    ) -> Optional[Any]:
        return deepcopy(
            self._response_values.get(survey_element_name, default_value)
        )

    def retrieve_all_responses(self) -> dict[str, Any]:
        return deepcopy(self._response_values)

    def clear(self):
        self._session.clear()

    @property
    def _visit_history(self) -> list[str]:
        visits = self._session.get(SurveySession.ELEMENT_VISITS)
        if visits is None:
            self._session[SurveySession.ELEMENT_VISITS] = visits = []
        return visits

    @property
    def _response_values(self) -> dict[str, Any]:
        values = self._session.get(SurveySession.ELEMENT_VALUES)
        if values is None:
            self._session[SurveySession.ELEMENT_VALUES] = values = {}
        return values
