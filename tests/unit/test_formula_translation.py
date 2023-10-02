import pytest

from survey_processor import SurveyProcessor


@pytest.mark.parametrize(
    "input_output",
    [
        # Test cases for translation of single equal sign
        ("a=1", "a==1"),
        ("a =1", "a ==1"),
        ("a = 1", "a == 1"),
        ("a!=1", "a!=1"),
        ("a<=1", "a<=1"),
        ("a = 1 and a <= 10 and a != 5", "a == 1 and a <= 10 and a != 5"),
        ("a= 1 and b= 2", "a== 1 and b== 2"),
        # Test cases for translation of dot expression
        (".<10", "self.curr_value<10"),
        ("5<.", "5<self.curr_value"),
        ("2.7<.", "2.7<self.curr_value"),
        ("2.7 <.", "2.7 <self.curr_value"),
        ("2.7< .", "2.7< self.curr_value"),
        ("2.7 < .", "2.7 < self.curr_value"),
        (
            "${some.variable} > 10 and . > 5.6",
            "${some.variable} > 10 and self.curr_value > 5.6",
        ),
        (r"regex(., '\p{L}')", r"regex(self.curr_value, '\p{L}')"),
        ("position(..)", "position(..)"),
    ],
)
def test_translate_xlsform_formula(input_output):
    input, output = input_output
    assert SurveyProcessor._translate_raw_formula(input) == output
