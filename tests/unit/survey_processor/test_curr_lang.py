from unittest.mock import PropertyMock

import pytest

from safely_report.survey.survey_processor import SurveyProcessor


@pytest.mark.parametrize(
    "current, default, options, expected",
    [
        # Return current language when it is set already
        ("english", "english", ["english", "french"], "english"),
        ("french", "english", ["english", "french"], "french"),
        # Return survey's default when the current language is not set
        ("", "english", ["english", "french"], "english"),
        ("", "french", ["english", "french"], "french"),
        # Return the first option when the current language is not set
        # and the survey's default does not exist in options
        ("", "default", ["english", "french"], "english"),
        ("", "default", ["french", "english"], "french"),
        # Return an empty string if the current language is not set
        # and there are no options available
        ("", "english", [], ""),
    ],
)
def test_curr_lang(
    # Fixture(s)
    mocker,
    survey_processor_instance,
    # Parameter(s)
    current,
    default,
    options,
    expected,
):
    processor = survey_processor_instance
    processor._session.language = current
    processor._survey.default_language = default
    mocker.patch.object(
        SurveyProcessor,
        "curr_lang_options",
        new_callable=PropertyMock,
        return_value=options,
    )

    assert processor.curr_lang == expected
