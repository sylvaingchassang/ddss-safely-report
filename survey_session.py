from typing import Any, Union

from werkzeug.local import LocalProxy


class SurveySession:
    """
    An interface to limit and structure interaction with the (server-side)
    session object.
    """

    ELEMENT_VISITS = "survey_elements_visited"
    ELEMENT_VALUES = "survey_response_values"

    def __init__(self, session: LocalProxy):
        self._session = session

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

    @property
    def latest_visit(self) -> Union[str, None]:
        if len(self._visit_history) > 0:
            return self._visit_history[-1]
        return None

    def drop_latest_visit(self):
        if len(self._visit_history) > 0:
            self._visit_history.pop()
            self._session.modified = True

    def add_new_visit(self, survey_element_name: str):
        self._visit_history.append(survey_element_name)
        self._session.modified = True

    def store_response(self, survey_element_name: str, response_value: Any):
        self._response_values[survey_element_name] = response_value
        self._session.modified = True

    def retrieve_response(self, survey_element_name: str) -> Union[Any, None]:
        return self._response_values.get(survey_element_name, None)
