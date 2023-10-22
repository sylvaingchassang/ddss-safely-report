from unittest.mock import MagicMock, Mock

import pytest
from pyxform.survey import Survey

from survey_processor import SurveyProcessor
from survey_session import SurveySession


@pytest.fixture(scope="function")
def survey_processor_instance():
    """
    An instance of `SurveyProcessor` with mock initiation.
    """
    survey = Mock(spec=Survey)
    survey.iter_descendants = MagicMock()
    survey_session = Mock(spec=SurveySession)
    survey_processor = SurveyProcessor(survey, survey_session)

    return survey_processor
