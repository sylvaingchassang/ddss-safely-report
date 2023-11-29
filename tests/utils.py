from survey_processor import SurveyProcessor


class MockFlaskSession(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = None


def instantiate_survey_processor(path_to_xlsform: str) -> SurveyProcessor:
    session = MockFlaskSession()
    survey_processor = SurveyProcessor(path_to_xlsform, session)
    return survey_processor
