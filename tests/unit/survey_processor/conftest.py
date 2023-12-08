import pytest
from pytest_mock import MockerFixture

from safely_report.survey.survey_processor import SurveyProcessor
from safely_report.survey.survey_session import SurveySession


@pytest.fixture(scope="function")
def survey_processor_instance(mocker: MockerFixture):
    """
    An instance of `SurveyProcessor` with mock initiation.
    """
    mocker.patch("safely_report.survey.survey_processor.read_xlsform")
    path_to_xlsform = ""
    survey_session = mocker.Mock(spec=SurveySession)
    survey_processor = SurveyProcessor(path_to_xlsform, survey_session)

    return survey_processor
