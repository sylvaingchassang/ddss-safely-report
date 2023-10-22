import pytest

from survey_processor import SurveyProcessor


@pytest.mark.parametrize(
    "input, output",
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
        (r"regex(., '\p{L}')", r"self._regex(self.curr_value, '\p{L}')"),
        ("position(..)", "self._position(..)"),  # TODO: Handle this outlier
        # Test cases for translation of XLSForm functions
        ("between(12, 100)", "self._between(12, 100)"),
        (
            "count-selected(.) <= 3",
            "self._count_selected(self.curr_value) <= 3",
        ),
        (
            "jr:choice-name( selected-at(${color-prefs}, 0), '${color-prefs}')",
            "self._jr_choice_name( self._selected_at(self.get_value('color-prefs'), 0), 'self.get_value('color-prefs')')",  # TODO: Handle this outlier
        ),
        # Test cases for translation of XLSForm variables
        ("${some-variable} > 10", "self.get_value('some-variable') > 10"),
        (
            ".!=${holiday.activity.1}",
            "self.curr_value!=self.get_value('holiday.activity.1')",
        ),
        (
            "selected(${ref65_intro}, '1')",
            "self._selected(self.get_value('ref65_intro'), '1')",
        ),
        (
            "${treatment_arm} in {4, 5, 6}",
            "self.get_value('treatment_arm') in {4, 5, 6}",
        ),
        (
            ". in { ${var.1}, ${var.2} }",
            "self.curr_value in { self.get_value('var.1'), self.get_value('var.2') }",
        ),
        # Advanced test cases
        (
            "${pa51_repeat}=0 or index()=1 and indexed-repeat(${pa51_repeat}, ${pa51},index()-1)!=0",
            "self.get_value('pa51_repeat')==0 or self._index()==1 and self._indexed_repeat(self.get_value('pa51_repeat'), self.get_value('pa51'),self._index()-1)!=0",
        ),
    ],
)
def test_translate_xlsform_formula(input, output):
    assert SurveyProcessor._translate_xlsform_formula(input) == output
