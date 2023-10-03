import re
from typing import Any

from pyxform import Question, Section, Survey
from pyxform.survey_element import SurveyElement

from survey_processor_base import SurveyProcessorBase


class SurveyProcessor(SurveyProcessorBase):
    def __init__(self, survey: Survey):
        self._survey = survey
        self._curr_node = self._survey.children[0]
        self._visit_history = [self._curr_node]
        self._responses = {}

    @property
    def curr_name(self) -> str:
        """
        Name of the current survey element.
        """
        return self._curr_node.name

    @property
    def curr_label(self) -> str:
        """
        Label of the current survey element (if applicable).
        """
        pass  # TODO: Implement

    @property
    def curr_hint(self) -> str:
        """
        Hint of the current survey element (if applicable).
        """
        pass  # TODO: Implement

    @property
    def curr_value(self) -> Any:
        """
        Response value of the current survey element (if applicable).
        """
        return self.get_value(self.curr_name)

    @property
    def curr_type(self) -> str:
        """
        Type of the current survey element (e.g., multiple-select question).
        """
        return self._curr_node.type

    @property
    def curr_to_show(self) -> bool:
        """
        Whether the current survey element is of a type to show to the
        respondent (e.g., note, multiple-select question).
        """
        pass  # TODO: Implement

    @property
    def curr_relevant(self) -> bool:
        """
        Whether the current survey element is relevant to the respondent.

        NOTE: This is different from `curr_to_show` property because a survey
        element can be of a type to show to the respondent (e.g., select-one
        question) yet not relevant to the respondent (e.g., respondent answered
        no to the prerequisite question), in which case the survey element will
        neither be shown nor executed at all.
        """
        formula_xlsform = self._curr_node.bind.get("relevant", None)
        if formula_xlsform is None:
            return True
        formula_python = self._translate_xlsform_formula(formula_xlsform)

        # TODO: Perform proper error handling
        return eval(formula_python)

    @property
    def curr_in_repeat(self) -> bool:
        """
        Whether the current survey element is in a repeat loop.
        """
        pass  # TODO: Implement

    def get_value(self, element_name: str) -> Any:
        """
        Get the response value of the given survey element.
        """
        value = self._responses.get(element_name, None)
        if value is None:
            raise KeyError(f"Value for {element_name} does not exist")
        return value

    @staticmethod
    def _translate_xlsform_formula(formula: str) -> str:
        """
        Translate XLSForm formula into the one that Python
        can evaluate.

        Given that XLSForm's formula uses a limited array of
        expressions, we can achieve accurate translation through
        RegEx-based text replacement.
        """
        # Compile a list of match-replace regex pairs
        regex_pairs = [
            # Replace single equal signs with double equal signs
            # while escaping other valid operators (`!=`, `>=`, `<=`)
            (r"([^\!\>\<]{1})=", r"\1=="),
            # Replace dots with the response value of the current survey
            # element (e.g., question) except for those that are part of
            # fractional numbers or part of variable names (i.e., wrapped
            # inside curly braces)
            (r"(?<!\d)(?<!\.)\.(?!\d)(?!\.)(?![^\{]*\})", "self.curr_value"),
            # Replace XLSForm functions (e.g., `selected-at()`) with
            # corresponding Python methods (e.g., `self._selected_at()`)
            (
                r"([a-z][a-z\d\:\-]*\()",
                lambda x: re.sub("[:-]", "_", "self._" + x.group(1)),
            ),
            # Replace XLSForm variables (e.g., `${some.var}`) with
            # Python expressions
            # NOTE: This replacement has to come AFTER replacement of
            # dot expressions AND replacement of XLSForm functions
            (r"(\$\{)([^\}]+)(\})", r"self.get_value('\2')"),
        ]

        # Perform translation
        for match_regex, replace_regex in regex_pairs:
            formula = re.sub(match_regex, replace_regex, formula)

        return formula

    def _get_next_sibling(self, element: SurveyElement) -> SurveyElement:
        """
        Return the immediate next sibling of the given survey element.
        """
        element_index = element.parent.children.index(element)
        return element.parent.children[element_index + 1]

    def next(self):
        """
        Move to the next survey element to process.
        """
        if isinstance(self._curr_node, Question):
            try:
                self._curr_node = self._get_next_sibling(self._curr_node)
            except IndexError:
                # If there is no more next sibling, move up to the parent node
                # and return its next sibling.
                self._curr_node = self._get_next_sibling(
                    self._curr_node.parent
                )
        elif isinstance(self._curr_node, Section):
            self._curr_node = self._curr_node.children[0]

        # Add the new node to visit history
        self._visit_history.append(self._curr_node)

    def back(self):
        """
        Move to the previously visited survey element.
        Note that we need to clear out visit history forward
        because changes in previous responses may change next questions.
        """
        if len(self._visit_history) > 1:
            self._visit_history.pop()  # Remove current node from visit history
            self._curr_node = self._visit_history[-1]
