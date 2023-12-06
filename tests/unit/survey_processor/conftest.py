import pytest

from safely_report.survey.survey_processor import SurveyProcessor


@pytest.fixture(scope="function")
def survey_processor_instance(mocker):
    """
    An instance of `SurveyProcessor` with mock initiation.
    """
    mocker.patch("safely_report.survey.survey_processor.read_xlsform")
    mocker.patch("safely_report.survey.survey_processor.SurveySession")
    survey_processor = SurveyProcessor("", {})

    return survey_processor
