import pytest


def test_get_existent_value(survey_processor_instance):
    processor = survey_processor_instance
    processor._session.retrieve_response.return_value = "value"
    assert processor.get_value("name") == "value"


def test_get_nonexistent_value(survey_processor_instance):
    processor = survey_processor_instance
    processor._session.retrieve_response.return_value = None
    with pytest.raises(KeyError):
        processor.get_value("name")
