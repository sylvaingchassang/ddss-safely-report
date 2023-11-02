from unittest.mock import MagicMock, Mock

import pytest
from pyxform.survey import Survey

from survey_processor import SurveyProcessor
from survey_session import SurveySession


@pytest.fixture(scope="function")
def survey_processor_instance(mocker):
    """
    An instance of `SurveyProcessor` with mock initiation.
    """
    mocker.patch("survey_processor.read_xlsform")
    mocker.patch("survey_processor.SurveySession")
    survey_processor = SurveyProcessor("", {})

    return survey_processor
