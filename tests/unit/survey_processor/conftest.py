from unittest.mock import MagicMock, Mock

import pytest
from pyxform.survey import Survey

from survey_processor import SurveyProcessor
from survey_session import SurveySession


@pytest.fixture(scope="function")
def survey_session_processor_instance():
    """
    An instance of `SurveyProcessor` with mock initiation.
    """
    survey = Mock(spec=Survey)
    survey.iter_descendants = MagicMock()
    session = Mock(spec=SurveySession)
    processor = SurveyProcessor(survey, session)

    return survey, session, processor
