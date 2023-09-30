import pytest

from survey_processor import SurveyProcessor


@pytest.mark.parametrize(
    "input_output",
    [
        ("a=1", "a==1"),
        ("a =1", "a ==1"),
        ("a = 1", "a == 1"),
        ("a!=1", "a!=1"),
        ("a<=1", "a<=1"),
        ("a = 1 and a <= 10 and a != 5", "a == 1 and a <= 10 and a != 5"),
        ("a= 1 and b= 2", "a== 1 and b== 2"),
    ],
)
def test_translate_single_equal_sign(input_output):
    input, output = input_output
    assert SurveyProcessor._translate_raw_formula(input) == output
