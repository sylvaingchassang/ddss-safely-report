from unittest.mock import PropertyMock

from safely_report.survey.survey_processor import SurveyProcessor


def test_set_curr_value_constraint_met(mocker, survey_processor_instance):
    processor = survey_processor_instance
    curr_name = "amount"
    curr_value = 10
    new_value = 20

    mocker.patch.object(
        SurveyProcessor,
        "_curr_constraint_met",
        new_callable=PropertyMock,
        return_value=True,
    )
    mocker.patch.object(
        SurveyProcessor,
        "curr_name",
        new_callable=PropertyMock,
        return_value=curr_name,
    )
    processor._session.retrieve_response.return_value = curr_value
    processor._session.store_response.return_value = None

    result = processor.set_curr_value(new_value)
    assert result is True
    processor._session.store_response.assert_called_with(curr_name, new_value)


def test_set_curr_value_constraint_not_met(mocker, survey_processor_instance):
    processor = survey_processor_instance
    curr_name = "amount"
    curr_value = 10
    new_value = 20

    mocker.patch.object(
        SurveyProcessor,
        "_curr_constraint_met",
        new_callable=PropertyMock,
        return_value=False,
    )
    mocker.patch.object(
        SurveyProcessor,
        "curr_name",
        new_callable=PropertyMock,
        return_value=curr_name,
    )
    processor._session.retrieve_response.return_value = curr_value
    processor._session.store_response.return_value = None

    result = processor.set_curr_value(new_value)
    assert result is False
    processor._session.store_response.assert_called_with(curr_name, curr_value)
