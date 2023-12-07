import pytest

from safely_report.survey.garbling import Garbler


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
