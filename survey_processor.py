import re
from typing import Any

from pyxform import Question, Section, Survey
from pyxform.survey_element import SurveyElement

from survey_processor_base import SurveyProcessorBase
from survey_session import SurveySession


class SurveyProcessor(SurveyProcessorBase):
    def __init__(self, survey: Survey, survey_session: SurveySession):
        self._survey = survey
        self._session = survey_session

        # Build a lookup table that maps element name to object
        # NOTE: This will NOT create too much memory overhead as the lookup
        # table simply stores references to objects, not copies of objects
        self._elements = {}
        for item in self._survey.iter_descendants():
            self._elements[item.name] = item

    @property
    def curr_lang_options(self) -> list[str]:
        """
        Language options for the current survey element.
        """
        label = self._curr_element.label
        if label == "":
            return []
        return list(label.keys())

    @property
    def curr_lang(self) -> str:
        """
        Language selected for the current survey element.
        """
        lang = self._session.language
        lang_options = self.curr_lang_options
        if len(lang_options) > 0 and lang == "":
            # Set to default
            default_lang = self._survey.default_language
            if default_lang not in lang_options:
                default_lang = lang_options[0]  # Randomly select
            self.set_curr_lang(default_lang)
            lang = self._session.language

        return lang

    def set_curr_lang(self, lang: str):
        """
        Set a new language for the current survey element.
        """
        if lang not in self.curr_lang_options:
            raise KeyError(f"{lang} is not a supported language")
        self._session.set_language(lang)

    def _get_element(self, element_name: str) -> SurveyElement:
        """
        Get the survey element object by its name.
        """
        element = self._elements.get(element_name, None)
        if element is None:
            raise KeyError(f"Element does not exist: {element_name}")
        return element

    def get_value(self, element_name: str) -> Any:
        """
        Get the response value of the given survey element.
        """
        value = self._session.retrieve_response(element_name)
        if value is None:
            raise KeyError(f"Value for {element_name} does not exist")
        return value

    @property
    def curr_name(self) -> str:
        """
        Name of the current survey element.
        """
        name = self._session.latest_visit
        if name is None:
            # Start from the beginning, i.e. survey root
            self._session.add_new_visit(self._survey.name)
            name = self._session.latest_visit
        return name

    @property
    def curr_value(self) -> Any:
        """
        Response value of the current survey element (if applicable).
        """
        return self.get_value(self.curr_name)

    @property
    def _curr_element(self) -> SurveyElement:
        """
        Current survey element object.
        """
        return self._get_element(self.curr_name)

    @property
    def curr_type(self) -> str:
        """
        Type of the current survey element (e.g., multiple-select question).
        """
        return self._curr_element.type

    @property
    def curr_label(self) -> str:
        """
        Label of the current survey element (if applicable).
        """
        label = self._curr_element.label
        if label == "":
            return label
        return label.get(self.curr_lang, "")

    @property
    def curr_hint(self) -> str:
        """
        Hint of the current survey element (if applicable).
        """
        hint = self._curr_element.hint
        if hint == "":
            return hint
        return hint.get(self.curr_lang, "")

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
        formula_xlsform = self._curr_element.bind.get("relevant", None)
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
        if isinstance(self._curr_element, Question):
            try:
                next_element = self._get_next_sibling(self._curr_element)
            except IndexError:
                # If there is no more next sibling, move up to the parent node
                # and return its next sibling.
                next_element = self._get_next_sibling(
                    self._curr_element.parent
                )
        elif isinstance(self._curr_element, Section):
            next_element = self._curr_element.children[0]

        # Update visit history
        self._session.add_new_visit(next_element.name)

    def back(self):
        """
        Move to the previously visited survey element.
        Note that we need to clear out visit history forward
        because changes in previous responses may change next questions.
        """
        self._session.drop_latest_visit()
