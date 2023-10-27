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
        if lang == "":
            lang_options = self.curr_lang_options
            if len(lang_options) > 0:
                lang = self._survey.default_language
                if lang not in lang_options:
                    lang = lang_options[0]  # Randomly select
                self._session.set_language(lang)

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
        if self._curr_element.bind.get("required") == "yes":
            return True
        return False

    @property
    def curr_to_show(self) -> bool:
        """
        Whether the current survey element is of a type to show to the
        respondent (e.g., note, multiple-select question).
        """
        return SurveyProcessor._find_whether_to_show(self._curr_element)

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
        formula = self._curr_element.bind.get("relevant")
        if formula is None:
            return True
        formula_py = SurveyProcessor._translate_xlsform_formula(formula)

        # TODO: Perform proper error handling
        return eval(formula_py)

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

        NOTE: Translation of XLSForm formula relies on this method,
        so any modification to this method should be done with care.
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
        curr_element = self._curr_element
        if isinstance(curr_element, Question):
            if len(curr_element.children) > 0:
                return [
                    (c.name, self._extract_text(c.label))
                    for c in curr_element.children
                ]

        return None

    def set_curr_lang(self, lang: str):
        """
        Set a new language for the current survey element.
        """
        if lang not in self.curr_lang_options:
            raise KeyError(f"{lang} is not a supported language")
        self._session.set_language(lang)

    def set_curr_value(self, new_value: Any) -> bool:
        """
        Updates the response value of the current survey element
        if the new value meets the constraint; existing value (if any)
        is retained if the constraint is not met.

        Returns
        -------
        bool
            True if the update was successful; False otherwise.
        """
        curr_name = self.curr_name
        curr_value = self._session.retrieve_response(curr_name)
        self._session.store_response(curr_name, new_value)
        if not self._curr_constraint_met:
            self._session.store_response(curr_name, curr_value)
            return False
        return True

    def get_value(self, element_name: str) -> Any:
        """
        Get the response value of the given survey element.

        NOTE: Translation of XLSForm formula relies on this method,
        so any modification to this method should be done with care.
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
        formula = self._curr_element.bind.get("constraint")
        if formula is None:
            return True
        formula_py = SurveyProcessor._translate_xlsform_formula(formula)

        # TODO: Perform proper error handling
        return eval(formula_py)

    def _get_element(self, element_name: str) -> SurveyElement:
        """
        Get the survey element object by its name.
        """
        element = self._elements.get(element_name)
        if element is None:
            raise KeyError(f"Element does not exist: {element_name}")
        return element

    def _position(self) -> int:
        """
        Return the number of times that the current survey element has been
        visited so far.

        This function replaces its XLSForm counterpart (i.e., `position(..)`).
        """
        return self._session.count_visits(self.curr_name)

    def _extract_text(self, field_content: Union[str, dict[str, str]]) -> str:
        """
        Extract "proper" text from a text-related field of a survey element.

        A text-related field in a survey element (constructed by `pyxform`)
        can contain either a single string value or a dictionary of multiple
        string values corresponding to different languages. This method handles
        this complexity and simply returns the most relevant piece of text.
        If nonexistent or not applicable, the method raises an error.
        """
        if isinstance(field_content, str):
            text = field_content
        elif isinstance(field_content, dict):
            if self.curr_lang not in field_content:
                raise Exception("Please select another language")
            text = field_content[self.curr_lang]
        else:
            raise Exception("The field does not contain text data")

        # Evaluate any XLSForm variables in the extracted text
        match = r"(\$\{)([^\}]+)(\})"
        replace = r"{self.get_value('\2')}"
        text = re.sub(match, replace, text)
        text = eval(f'f"{text}"')

        return text

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

        formula = curr_element.bind.get("calculate")
        if formula is not None:
            formula_py = SurveyProcessor._translate_xlsform_formula(formula)
            self.set_curr_value(eval(formula_py))

    def _execute_repeat(self):
        """
        Update session states for the new iteration of the repeat.
        """
        curr_element = self._curr_element
        if curr_element.type != "repeat":
            return

        n_repeat = self._session.count_visits(curr_element.name)
        for child_element in curr_element.iter_descendants():
            if SurveyProcessor._find_whether_to_show(child_element):
                # Get name and value of the element
                varname = child_element.name
                value = self._session.retrieve_response(varname)

                # Get name and value of the element's "auxiliary" store
                # that contains all repeated responses to the element
                repeat_varname = SurveyProcessor._term_repeat_varname(varname)
                value_lst = self._session.retrieve_response(repeat_varname, [])

                # Store incumbent value into previous iteration version
                try:
                    value_lst[n_repeat - 2] = value  # Zero-indexed
                except IndexError:
                    value_lst.append(value)
                self._session.store_response(repeat_varname, value_lst)

                # Update incumbent value with current iteration version
                try:
                    value = value_lst[n_repeat - 1]  # Zero-indexed
                except IndexError:
                    value = None
                self._session.store_response(varname, value)

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

        n_repeat = self._session.count_visits(curr_element.name)
        for child_element in curr_element.iter_descendants():
            if SurveyProcessor._find_whether_to_show(child_element):
                # Get name and value of the element
                varname = child_element.name
                value = self._session.retrieve_response(varname)

                # Get name and value of the element's "auxiliary" store
                # that contains all repeated responses to the element
                repeat_varname = SurveyProcessor._term_repeat_varname(varname)
                value_lst = self._session.retrieve_response(repeat_varname, [])

                # Update incumbent value with previous iteration version
                try:
                    value = value_lst[n_repeat - 2]  # Zero-indexed
                except IndexError:
                    value = None
                self._session.store_response(varname, value)

    def _next(self):
        """
        Move to the next survey element.
        """
        curr_element = self._curr_element

        # Determine the next element
        if isinstance(curr_element, Section) and self.curr_relevant:
            if curr_element.type == "repeat":
                n_repeat = self._session.count_visits(curr_element.name)
                limit = curr_element.control.get("jr:count", "float('inf')")
                limit = eval(SurveyProcessor._translate_xlsform_formula(limit))
                if n_repeat <= limit:
                    next_element = curr_element.children[0]
                else:
                    self._clean_obsolete_repeat_responses()
                    next_element = self._get_next_sibling(curr_element)
            else:
                next_element = curr_element.children[0]
        else:
            next_element = self._get_next_sibling(curr_element)

        # Update visit history
        self._session.add_new_visit(next_element.name)

    def _clean_obsolete_repeat_responses(self):
        """
        Remove any obsolete "excess" repeat responses under the current
        repeat section.

        NOTE: Obsolete "excess" repeat responses may result from the respondent
        already submitting repeat responses and then decreasing the number of
        "valid" repeats by modifying related previous responses.
        """
        curr_element = self._curr_element
        if curr_element.type != "repeat":
            return

        n_repeat = self._session.count_visits(curr_element.name)
        for child_element in curr_element.iter_descendants():
            if SurveyProcessor._find_whether_to_show(child_element):
                # Get name and value of the element's "auxiliary" store
                # that contains all repeated responses to the element
                varname = child_element.name
                repeat_varname = SurveyProcessor._term_repeat_varname(varname)
                value_lst = self._session.retrieve_response(repeat_varname, [])

                # If there are "excess" responses, cut them out
                if len(value_lst) >= n_repeat:
                    value_lst_sub = value_lst[: n_repeat - 1]  # Zero-indexed
                    self._session.store_response(repeat_varname, value_lst_sub)

    def _back(self):
        """
        Move to the previously visited survey element.
        Note that we need to clear out visit history forward
        because changes in previous responses may change next questions.
        """
        self._session.drop_latest_visit()

    @staticmethod
    def _find_whether_to_show(element: SurveyElement) -> bool:
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

    def _get_next_sibling(self, element: SurveyElement) -> SurveyElement:
        """
        Return the immediate next sibling of the given survey element.
        - If there is no more next sibling, move up to the parent node
        and return its next sibling.
        - If the given survey element is the survey root, simply return
        itself as the survey root does not have any sibling or parent.
        """
        if element.name == self._survey.name:  # Survey root
            return element

        element_index = element.parent.children.index(element)
        try:
            return element.parent.children[element_index + 1]
        except IndexError:
            if element.parent.type == "repeat":
                return element.parent
            else:
                return self._get_next_sibling(element.parent)

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
            # Replace a single dot with the response value of the current
            # survey element (e.g., question) except for those that are part
            # of fractional numbers or part of variable names (i.e., wrapped
            # inside curly braces)
            (r"(?<!\d)(?<!\.)\.(?!\d)(?!\.)(?![^\{]*\})", "self.curr_value"),
            # Remove double-dot path operator (`..`)
            # NOTE: The operator logic will be directly implemented into any
            # function that uses it (e.g., `position(..)`)
            (r"(?<!\.)\.\.(?!\.)", ""),
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
    def _term_repeat_varname(element_name: str):
        """
        Create name to use to store repeat responses to the given question.
        """
        return f"{element_name}::REPEATS"
