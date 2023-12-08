from safely_report.survey.survey_processor import SurveyProcessor
from safely_report.survey.survey_session import SurveySession


class MockFlaskSession(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = None


def instantiate_survey_processor(path_to_xlsform: str) -> SurveyProcessor:
    session = MockFlaskSession()
    survey_session = SurveySession(session)  # type: ignore
    survey_processor = SurveyProcessor(path_to_xlsform, survey_session)
    return survey_processor
