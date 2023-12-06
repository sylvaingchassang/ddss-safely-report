import pytest

from safely_report.survey.survey_processor import SurveyProcessor


@pytest.fixture
def processor(processor_for_holidays_survey) -> SurveyProcessor:
    return processor_for_holidays_survey


def test_survey_start(processor: SurveyProcessor):
    assert processor.curr_survey_start is True


def test_survey_next(processor: SurveyProcessor):
    processor.next()
    assert processor.curr_name == "intro.note"
    processor.next()
    assert processor.curr_name == "name"
    processor.next()
    assert processor.curr_name == "date.birth"


def test_survey_end(processor: SurveyProcessor):
    processor.next()
    processor._session.add_new_visit("holiday.activity.3")
    processor.next()
    assert processor.curr_survey_end is True
