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
            "self.get_value('some.variable') > 10 and self.curr_value > 5.6",
        ),
        (r"regex(., '\p{L}')", r"regex(self.curr_value, '\p{L}')"),
        ("position(..)", "position(..)"),
        # Test cases for translation of XLSForm variables
        ("${some-variable} > 10", "self.get_value('some-variable') > 10"),
        (
            ".!=${holiday.activity.1}",
            "self.curr_value!=self.get_value('holiday.activity.1')",
        ),
        (
            "selected(${ref65_intro}, '1')",
            "selected(self.get_value('ref65_intro'), '1')",
        ),
        (
            "${treatment_arm} in {4, 5, 6}",
            "self.get_value('treatment_arm') in {4, 5, 6}",
        ),
        (
            ". in { ${var.1}, ${var.2} }",
            "self.curr_value in { self.get_value('var.1'), self.get_value('var.2') }",
        ),
    ],
)
def test_translate_xlsform_formula(input_output):
    input, output = input_output
    assert SurveyProcessor._translate_raw_formula(input) == output
