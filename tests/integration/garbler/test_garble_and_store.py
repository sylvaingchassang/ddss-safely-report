import pytest
from flask_sqlalchemy import SQLAlchemy
from pytest_mock import MockerFixture

from safely_report.models import Respondent, SurveyResponse
from safely_report.survey.garbling import Garbler, GarblingParams
from safely_report.utils import deserialize


@pytest.fixture
def garbler(mocker: MockerFixture, test_db: SQLAlchemy) -> Garbler:
    mocker.patch.object(
        Garbler,
        "_parse_xlsform",
        return_value={},
    )
    path_to_xlsform = ""
    garbler = Garbler(path_to_xlsform, test_db)

    return garbler


def test_iid_garbling_working(garbler: Garbler, test_db: SQLAlchemy):
    # Set up IID garbling with a high rate
    garbling_params = GarblingParams(
        question="question",
        answer="yes",
        rate=1.0,
        covariate=None,
    )
    garbler._params[garbling_params.question] = garbling_params

    for _ in range(10):
        # Create a respondent record in database
        respondent = Respondent()
        test_db.session.add(respondent)
        test_db.session.commit()

        # Submit survey response that goes against garbling answer
        survey_response = {garbling_params.question: "no"}
        respondent_uuid = str(respondent.uuid)
        garbler.garble_and_store(survey_response, respondent_uuid)

    # Count garbled survey responses
    n_garbled = 0
    survey_responses = SurveyResponse.query.all()
    for r in survey_responses:
        r = deserialize(r.response)
        if r[garbling_params.question] == garbling_params.answer:
            n_garbled += 1

    # Check if garbling had an effect
    assert n_garbled == 10


@pytest.mark.parametrize(
    "n_report, garbling_rate, n_garbled_expected",
    [
        (10, 0.2, 2),
        (10, 0.4, 4),
        (10, 0.5, 5),
        (10, 0.6, 6),
        (10, 0.8, 8),
    ],
)
def test_block_garbling_consistency(
    # Fixture(s)
    garbler: Garbler,
    test_db: SQLAlchemy,
    # Parameter(s)
    n_report: int,
    garbling_rate: float,
    n_garbled_expected: int,
):
    # Set up population-blocked garbling
    garbling_params = GarblingParams(
        question="question",
        answer="yes",
        rate=garbling_rate,
        covariate="*",
    )
    garbler._params[garbling_params.question] = garbling_params

    for _ in range(n_report):
        # Create a respondent record in database
        respondent = Respondent()
        test_db.session.add(respondent)
        test_db.session.commit()

        # Submit survey response that goes against garbling answer
        survey_response = {garbling_params.question: "no"}
        respondent_uuid = str(respondent.uuid)
        garbler.garble_and_store(survey_response, respondent_uuid)

    # Count garbled survey responses
    n_garbled = 0
    survey_responses = SurveyResponse.query.all()
    for r in survey_responses:
        r = deserialize(r.response)
        if r[garbling_params.question] == garbling_params.answer:
            n_garbled += 1

    # Compare against expected number of garbling
    assert n_garbled == n_garbled_expected
