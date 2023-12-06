from typing import Union

import pytest
from pytest_mock import MockerFixture

from safely_report.survey.garbling import Garbler, GarblingScheme


@pytest.mark.parametrize(
    "garbling_answer, garbling_shock, response_value, garbled_value_expected",
    [
        ("yes", True, "yes", "yes"),
        ("yes", True, "no", "yes"),
        ("yes", False, "yes", "yes"),
        ("yes", False, "no", "no"),
    ],
)
def test_garble_response(
    # Parameter(s)
    garbling_answer: str,
    garbling_shock: bool,
    response_value: str,
    garbled_value_expected: str,
):
    garbled_value = Garbler._garble_response(
        garbling_answer, garbling_shock, response_value
    )
    assert garbled_value == garbled_value_expected


@pytest.mark.parametrize(
    "garbling_answer, garbling_rate, random_number, response_value, garbled_value_expected, garbling_counter_expected",
    [
        # Garbling is applied if garbling_rate > random_number
        ("yes", 0.3, 0.1, "yes", "yes", 1),
        ("yes", 0.3, 0.1, "no", "yes", 1),
        ("yes", 0.3, 0.9, "yes", "yes", 0),
        ("yes", 0.3, 0.9, "no", "no", 0),
    ],
)
def test_garble_individual_response(
    mocker: MockerFixture,
    # Parameter(s)
    garbling_answer: str,
    garbling_rate: float,
    random_number: float,
    response_value: str,
    garbled_value_expected: str,
    garbling_counter_expected: int,
):
    mocker.patch(
        "safely_report.survey.garbling.random",
        return_value=random_number,
    )
    garbling_params = mocker.Mock()
    garbling_params.answer = garbling_answer
    garbling_params.rate = garbling_rate
    garbling_params.scheme = GarblingScheme.IID

    garbled_value, garbling_counter = Garbler.garble_individual_response(
        garbling_params=garbling_params,
        response_value=response_value,
    )

    assert garbled_value == garbled_value_expected
    assert garbling_counter == garbling_counter_expected


def test_garble_individual_response_with_wrong_scheme(mocker: MockerFixture):
    garbling_params = mocker.Mock()
    garbling_params.scheme = GarblingScheme.PopBlock
    response_values = mocker.MagicMock()
    with pytest.raises(Exception):
        Garbler.garble_individual_response(garbling_params, response_values)


@pytest.mark.parametrize(
    "garbling_answer, garbling_rate, response_values, garbled_values_expected, garbling_counter_expected",
    [
        # For testing, garbling is applied to first K response values
        ("y", 0.2, ["n", "y", "n", "y"], ["y", "y", "n", "y"], 1),
        ("y", 0.3, ["n", "y", "n", "y"], ["y", "y", "n", "y"], 2),
        ("y", 0.3, ["n", None, "n", "y"], ["y", None, "n", "y"], 1),
        ("y", 0.6, ["n", None, "n", "y"], ["y", None, "y", "y"], 2),
        ("y", 0.6, ["n", "y", "n", "y"], ["y", "y", "y", "y"], 3),
    ],
)
def test_garble_block_responses(
    mocker: MockerFixture,
    # Parameter(s)
    garbling_answer: str,
    garbling_rate: float,
    response_values: list[Union[str, None]],
    garbled_values_expected: list[Union[str, None]],
    garbling_counter_expected: int,
):
    mocker.patch("safely_report.survey.garbling.shuffle")
    garbling_params = mocker.Mock()
    garbling_params.answer = garbling_answer
    garbling_params.rate = garbling_rate
    garbling_params.scheme = GarblingScheme.PopBlock

    garbled_values, garbling_counter = Garbler.garble_block_responses(
        garbling_params=garbling_params,
        response_values=response_values,
    )

    assert garbled_values == garbled_values_expected
    assert garbling_counter == garbling_counter_expected


def test_garble_block_responses_with_wrong_scheme(mocker: MockerFixture):
    garbling_params = mocker.Mock()
    garbling_params.scheme = GarblingScheme.IID
    response_values = mocker.MagicMock()
    with pytest.raises(Exception):
        Garbler.garble_block_responses(garbling_params, response_values)
