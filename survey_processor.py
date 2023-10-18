import re
from typing import Any, Optional, Union

from pyxform import Question, Section, Survey
from pyxform.survey_element import SurveyElement

from survey_processor_base import SurveyProcessorBase
from survey_session import SurveySession


class SurveyProcessor(SurveyProcessorBase):
    """
    A survey processing engine that moves between different survey elements
    and controls their properties to run the survey.

    NOTE: `SurveyProcessor` is "stateless" as it caches client data
    (e.g., current location in the survey) in server-side sessions via
    `SurveySession`.
    """

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

    @property
    def curr_type(self) -> str:
        """
        Type of the current survey element (e.g., multiple-select question).
        """
        return self._curr_element.type

    @property
    def curr_required(self) -> bool:
        """
        Whether response to the current survey element is required.
        """
        if self._curr_element.bind.get("required", "") == "yes":
            return True
        return False

    @property
    def curr_to_show(self) -> bool:
        """
        Whether the current survey element is of a type to show to the
        respondent (e.g., note, multiple-select question).
        """
        return self._is_to_show(self._curr_element)

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
    def curr_name(self) -> str:
        """
        Name of the current survey element.
        """
        if self._session.latest_visit is None:
            # Start from the beginning, i.e. survey root
            self._session.add_new_visit(self._survey.name)
            self.next()  # Roll forward to the first displayable element
        return self._session.latest_visit  # type: ignore

    @property
    def curr_value(self) -> Any:
        """
        Response value of the current survey element (if applicable).
        """
        return self.get_value(self.curr_name)

    @property
    def curr_label(self) -> str:
        """
        Label of the current survey element.

        If not applicable, an empty string is returned.
        """
        return self._extract_text(self._curr_element.label)

    @property
    def curr_hint(self) -> str:
        """
        Hint of the current survey element.

        If not applicable, an empty string is returned.
        """
        return self._extract_text(self._curr_element.hint)

    @property
    def curr_constraint_message(self) -> str:
        """
        Constraint message for the current survey element.

        If not applicable, an empty string is returned.
        """
        field_content = self._curr_element.bind.get("jr:constraintMsg", "")
        return self._extract_text(field_content)

    @property
    def curr_choices(self) -> Optional[list[tuple[str, str]]]:
        """
        Return the current survey element's choices/options if applicable.
        If none or not applicable, return nothing.
        """
        if isinstance(self._curr_element, Question):
            if len(self._curr_element.children) > 0:
                return [
                    (c.name, self._extract_text(c.label))
                    for c in self._curr_element.children
                ]

        return None

    def set_curr_lang(self, lang: str):
        """
        Set a new language for the current survey element.
        """
        if lang not in self.curr_lang_options:
            raise KeyError(f"{lang} is not a supported language")
        self._session.set_language(lang)

    def set_curr_value(self, value: Any) -> bool:
        """
        Updates the response value of the current survey element
        if the new value meets the constraint; existing value (if any)
        is retained if the constraint is not met.

        Returns
        -------
        bool
            True if the update was successful; False otherwise.
        """
        prev_value = self._session.retrieve_response(self.curr_name)
        self._session.store_response(self.curr_name, value)
        if self._curr_constraint_met is False:
            if prev_value is not None:
                self._session.store_response(self.curr_name, prev_value)
            return False
        return True

    def get_value(self, element_name: str) -> Any:
        """
        Get the response value of the given survey element.
        """
        value = self._session.retrieve_response(element_name)
        if value is None:
            raise KeyError(f"Value for {element_name} does not exist")
        return value

    def next(self):
        """
        Move to the next relevant survey element to show to the respondent.
        """
        while True:
            # If the current survey element is relevant, execute it
            if self.curr_relevant:
                self._execute()

            # Move to the next survey element
            self._next()

            # Repeat steps above until the new element is both relevant and
            # of a type to display to the respondent
            if self.curr_relevant and self.curr_to_show:
                break

    def back(self):
        """
        Move to the previous relevant survey element to show to the respondent.
        """
        while True:
            # If the current survey element is relevant, reverse-execute it
            if self.curr_relevant:
                self._revert()

            # Move to the previous survey element
            self._back()

            # If reaching the survey root, roll forward to the first
            # displayable element
            if self.curr_name == self._survey.name:
                self.next()
                break

            # Repeat steps above until the new element is both relevant and
            # of a type to display to the respondent
            if self.curr_relevant and self.curr_to_show:
                break

    @property
    def _curr_element(self) -> SurveyElement:
        """
        Current survey element object.
        """
        return self._get_element(self.curr_name)

    @property
    def _curr_constraint_met(self) -> bool:
        """
        Whether the response value of the current survey element meets
        the constraint (if any).
        """
        formula_xlsform = self._curr_element.bind.get("constraint", None)
        if formula_xlsform is None:
            return True
        formula_python = self._translate_xlsform_formula(formula_xlsform)

        # TODO: Perform proper error handling
        return eval(formula_python)

    def _get_element(self, element_name: str) -> SurveyElement:
        """
        Get the survey element object by its name.
        """
        element = self._elements.get(element_name, None)
        if element is None:
            raise KeyError(f"Element does not exist: {element_name}")
        return element

    def _extract_text(self, field_content: Union[str, dict[str, str]]) -> str:
        """
        Extract "proper" text from a text-related field of a survey element.

        A text-related field in a survey element (constructed by `pyxform`)
        can contain either a single string value or a dictionary of multiple
        string values corresponding to different languages. This method handles
        this complexity and simply returns the most relevant piece of text.
        If nonexistent or not applicable, the method returns an empty string.
        """
        if isinstance(field_content, str):
            return field_content
        if isinstance(field_content, dict):
            return field_content.get(self.curr_lang, "")
        else:
            return ""

    def _execute(self):
        """
        Execute session-state modifications (e.g., calculation) encoded
        in the current survey element.
        """
        self._execute_calculate()
        self._execute_repeat()

    def _execute_calculate(self):
        """
        Execute calculation in the current survey element.

        NOTE: If calculations happen in question-type elements, the calculated
        value will overwrite the initial response value, which may result in
        undesirable issues. Hence, we allow calculations to take effect only in
        elements of the "calculate" type.
        """
        curr_element = self._curr_element
        if curr_element.type != "calculate":
            return

        formula_xlsform = curr_element.bind.get("calculate", None)
        if formula_xlsform is None:
            return
        formula_python = self._translate_xlsform_formula(formula_xlsform)
        self.set_curr_value(eval(formula_python))

    def _execute_repeat(self):
        """
        Update session states for the new iteration of the repeat.
        """
        curr_element = self._curr_element
        if curr_element.type != "repeat":
            return

        n = self._session.count_visit(curr_element.name)
        for child_element in curr_element.iter_descendants():
            if self._is_to_show(child_element):
                name = child_element.name
                value = self._session.retrieve_response(name)

                # Store incumbent value into previous iteration version
                name_prev_repeat = self._name_repeat_response(name, n - 1)
                self._session.store_response(name_prev_repeat, value)

                # Update incumbent value with current iteration version
                name_curr_repeat = self._name_repeat_response(name, n)
                new_value = self._session.retrieve_response(name_curr_repeat)
                self._session.store_response(name, new_value)

    def _revert(self):
        """
        Reverse session-state modifications made in the current survey element.
        """
        self._revert_repeat()

    def _revert_repeat(self):
        """
        Update session states to roll back to the previous iteration
        of the repeat.
        """
        curr_element = self._curr_element
        if curr_element.type != "repeat":
            return

        n = self._session.count_visit(curr_element.name)
        for child_element in curr_element.iter_descendants():
            if self._is_to_show(child_element):
                name = child_element.name
                value = self._session.retrieve_response(name)

                # Store incumbent value into current iteration version
                name_curr_repeat = self._name_repeat_response(name, n)
                self._session.store_response(name_curr_repeat, value)

                # Update incumbent value with previous iteration version
                name_prev_repeat = self._name_repeat_response(name, n - 1)
                new_value = self._session.retrieve_response(name_prev_repeat)
                self._session.store_response(name, new_value)

    def _next(self):
        """
        Move to the next survey element.
        """
        curr_element = self._curr_element

        # Determine the next element
        if isinstance(curr_element, Section) and self.curr_relevant:
            if curr_element.type == "repeat":
                n = self._session.count_visit(curr_element.name)
                limit = curr_element.control.get("jr:count", "float('inf')")
                limit = eval(self._translate_xlsform_formula(limit))
                if n <= limit:
                    next_element = curr_element.children[0]
                else:
                    next_element = self._get_next_sibling(curr_element)
            else:
                next_element = curr_element.children[0]
        else:
            next_element = self._get_next_sibling(curr_element)

        # Update visit history
        self._session.add_new_visit(next_element.name)

    def _back(self):
        """
        Move to the previously visited survey element.
        Note that we need to clear out visit history forward
        because changes in previous responses may change next questions.
        """
        self._session.drop_latest_visit()

    @staticmethod
    def _is_to_show(element: SurveyElement) -> bool:
        """
        Determine whether the given survey element is of a type to show to
        the respondent (e.g., note, multiple-select question).

        We leverage `pyxform` package's classification to identify such
        elements. Specifically, `pyxform` assigns more concrete subclasses
        (e.g., `InputQuestion`, `MultipleChoiceQuestion`) to survey elements
        that are "real" questions to display to the respondent; and it uses
        generic `Question` class for elements related to internal actions
        such as calculation.
        """
        if isinstance(element, Question) and type(element) != Question:
            return True
        return False

    @staticmethod
    def _get_next_sibling(element: SurveyElement) -> SurveyElement:
        """
        Return the immediate next sibling of the given survey element.
        If there is no more next sibling, move up to the parent node
        and return its next sibling.
        """
        element_index = element.parent.children.index(element)
        try:
            return element.parent.children[element_index + 1]
        except IndexError:
            if element.parent.type == "repeat":
                return element.parent
            else:
                return SurveyProcessor._get_next_sibling(element.parent)

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
                lambda x: "self._" + re.sub("[:-]", "_", x.group(1)),
            ),
            # Replace XLSForm variables (e.g., `${some.var}`) with
            # Python expressions
            # NOTE: This replacement has to come AFTER replacement of
            # dot expressions AND replacement of XLSForm functions
            (r"(\$\{)([^\}]+)(\})", r"self.get_value('\2')"),
        ]

        # Perform translation
        for match, replace in regex_pairs:
            formula = re.sub(match, replace, formula)  # type: ignore

        return formula

    @staticmethod
    def _name_repeat_response(element_name: str, repeat_turn_i: int):
        """
        Create name to use to store i-th response to the given question.
        """
        return f"{element_name}:REPEAT:#{repeat_turn_i}"
