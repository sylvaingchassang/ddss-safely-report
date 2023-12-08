import pytest

from safely_report.survey.garbling import Garbler


@pytest.mark.parametrize(
    "response_value, garbling_shock, garbling_answer, garbled_value_expected",
    [
        ("yes", True, "yes", "yes"),
        ("no", True, "yes", "yes"),
        ("yes", False, "yes", "yes"),
        ("no", False, "yes", "no"),
    ],
)
def test_garble_response(
    # Parameter(s)
    response_value: str,
    garbling_shock: bool,
    garbling_answer: str,
    garbled_value_expected: str,
):
    garbled_value = Garbler._garble_response(
        response_value, garbling_shock, garbling_answer
    )
    assert garbled_value == garbled_value_expected
