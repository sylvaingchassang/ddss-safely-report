import pytest

from survey_processor import SurveyProcessor


@pytest.fixture(scope="function")
def survey_processor_instance(mocker):
    """
    An instance of `SurveyProcessor` with mock initiation.
    """
    mocker.patch("survey_processor.read_xlsform")
    mocker.patch("survey_processor.SurveySession")
    survey_processor = SurveyProcessor("", {})

    return survey_processor
