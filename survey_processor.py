from pyxform.survey_element import SurveyElement
from pyxform import Survey, Section, Question

class SurveyProcessor:
    def __init__(self, survey: Survey):
        self._survey = survey
        self._curr_node = self._survey.children[0]
        self._visit_history = [self._curr_node]

    @property
    def curr_name(self) -> str:
        return self._curr_node.name

    @property
    def curr_type(self) -> str:
        return self._curr_node.type

    def _get_next_sibling(self, element: SurveyElement) -> SurveyElement:
        """
        Return the immediate next sibling of the given survey element.
        """
        element_index = element.parent.children.index(element)
        return element.parent.children[element_index+1]

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
                self._curr_node = self._get_next_sibling(self._curr_node.parent)
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
