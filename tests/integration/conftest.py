import pytest

from safely_report.survey.survey_processor import SurveyProcessor
from tests.utils import instantiate_survey_processor


@pytest.fixture
def processor_for_holidays_survey() -> SurveyProcessor:
    path_to_xlsform = "tests/data/stats4sd_example_xlsform_adapted.xlsx"
    return instantiate_survey_processor(path_to_xlsform)
