from random import choices

import pytest
from flask_sqlalchemy import SQLAlchemy
from pytest_mock import MockerFixture
from sqlalchemy.exc import IntegrityError

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


def test_iid_garbling(garbler: Garbler, test_db: SQLAlchemy):
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
def test_population_blocked_garbling(
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

    # Create and submit survey responses
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
def test_covariate_blocked_garbling(
    # Fixture(s)
    garbler: Garbler,
    test_db: SQLAlchemy,
    # Parameter(s)
    n_report: int,
    garbling_rate: float,
    n_garbled_expected: int,
):
    # Set up covariate-blocked garbling
    garbling_params = GarblingParams(
        question="question",
        answer="yes",
        rate=garbling_rate,
        covariate="team",
    )
    garbler._params[garbling_params.question] = garbling_params

    for _ in range(n_report):
        # Consider various covariate blocks (with "A" being the test target)
        team_lst = ["A"] + choices(["B", "C", "D"], k=2)

        # Create and submit survey responses
        for team in team_lst:
            # Create a respondent record in database
            respondent = Respondent(team=team)
            test_db.session.add(respondent)
            test_db.session.commit()

            # Submit survey response that goes against garbling answer
            survey_response = {garbling_params.question: "no"}
            respondent_uuid = str(respondent.uuid)
            garbler.garble_and_store(survey_response, respondent_uuid)

    # Count garbled survey responses within the target covariate block
    n_garbled = 0
    survey_responses = (
        SurveyResponse.query.join(Respondent)
        .filter(Respondent.team == "A")
        .all()
    )
    for r in survey_responses:
        r = deserialize(r.response)
        if r[garbling_params.question] == garbling_params.answer:
            n_garbled += 1

    # Compare against expected number of garbling
    assert len(survey_responses) == n_report
    assert n_garbled == n_garbled_expected


def test_covariate_blocked_garbling_with_missing_covariate_value(
    garbler: Garbler, test_db: SQLAlchemy
):
    # Set up covariate-blocked garbling
    garbling_params = GarblingParams(
        question="question",
        answer="yes",
        rate=0.4,
        covariate="team",
    )
    garbler._params[garbling_params.question] = garbling_params

    # Create a respondent record in database
    respondent = Respondent()  # Missing covariate value
    test_db.session.add(respondent)
    test_db.session.commit()

    # Submit survey response that goes against garbling answer
    survey_response = {garbling_params.question: "no"}
    respondent_uuid = str(respondent.uuid)
    garbler.garble_and_store(survey_response, respondent_uuid)

    # Confirm stored survey response has no data for the considered question
    assert SurveyResponse.query.count() == 1
    response_record = SurveyResponse.query.first()
    assert response_record.respondent_uuid == respondent_uuid
    stored_response = deserialize(response_record.response)
    assert stored_response.get(garbling_params.question, None) is None


def test_response_resubmission(garbler: Garbler, test_db: SQLAlchemy):
    # Create a respondent record in database
    respondent = Respondent()
    test_db.session.add(respondent)
    test_db.session.commit()

    # Submit survey response
    survey_response = {"color": "green"}
    respondent_uuid = str(respondent.uuid)
    garbler.garble_and_store(survey_response, respondent_uuid)

    # Confirm submitted response has been stored
    assert SurveyResponse.query.count() == 1
    assert SurveyResponse.query.first().respondent_uuid == respondent_uuid

    # Confirm response resubmission fails
    with pytest.raises(IntegrityError):
        new_survey_response = {"color": "red"}
        garbler.garble_and_store(new_survey_response, respondent_uuid)
