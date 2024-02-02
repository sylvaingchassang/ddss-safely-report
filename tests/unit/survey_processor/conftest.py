import pytest
from flask.sessions import SessionMixin
from pytest_mock import MockerFixture

from safely_report.survey.survey_processor import SurveyProcessor


@pytest.fixture(scope="function")
def survey_processor_instance(mocker: MockerFixture):
    """
    An instance of `SurveyProcessor` with mock initiation.
    """
    mocker.patch("safely_report.survey.survey_processor.read_xlsform")
    mocker.patch("safely_report.survey.survey_processor.SurveySession")
    path_to_xlsform = ""
    session = mocker.Mock(spec=SessionMixin)
    survey_processor = SurveyProcessor(path_to_xlsform, session)

    return survey_processor
