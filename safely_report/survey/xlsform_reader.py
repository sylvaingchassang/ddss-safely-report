import re

from pyxform import Question, Survey
from pyxform.builder import create_survey_element_from_dict
from pyxform.survey_element import SurveyElement
from pyxform.xls2json import parse_file_to_json


class XLSFormReader:
    @classmethod
    def read_xlsform(cls, path_to_xlsform: str) -> Survey:
        """
        Parse and validate XLSForm to generate its Python representation.

        Parameters
        ----------
        path_to_xlsform: str
            Path to the XLSForm file specifying the survey
        """
        # Parse the form
        survey_dict = parse_file_to_json(
            path=path_to_xlsform,
            default_name="__survey__",
        )
        survey = create_survey_element_from_dict(survey_dict)

        # Validate the form meets requirements specific to our application
        assert isinstance(survey, Survey)
        for element in survey.iter_descendants():
            cls._check_infinite_repeat(element)
            cls._check_nested_repeat(element)
            cls._check_supported_question(element)
            cls._check_functions(element)

        return survey

    @classmethod
    def _check_infinite_repeat(cls, element: SurveyElement):
        """
        Error out if the given survey element is an infinite repeat.

        The application does not support infinite repeats for now. Instead,
        survey designers can use repeats where the respondent can dynamically
        set and change the number of repeats. For instance, if the survey has
        a repeat section asking details of family members (e.g., name, age),
        it can first ask how many family members the respondent has and then,
        based on this response, perform repeats.
        """
        if element.type == "repeat":
            if element.control.get("jr:count") is None:
                raise Exception(f"Infinite repeat not allowed: {element.name}")

    @classmethod
    def _check_nested_repeat(cls, element: SurveyElement):
        """
        Error out if the given survey element is a nested repeat.

        The application does not support nested repeats (i.e., repeat section
        within another repeat section); it only supports single-depth repeats.
        We made this choice because nested repeats introduce unnecessary
        complication to survey administration itself.
        """
        if element.type == "repeat":
            for descendant in element.iter_descendants():
                if descendant != element and descendant.type == "repeat":
                    raise Exception(
                        f"Nested repeat not allowed: {element.name}"
                    )

    @classmethod
    def _check_supported_question(cls, element: SurveyElement):
        """
        Error out if the given survey element is an unsupported question type.

        We leverage `pyxform` package's classification to identify survey
        elements that are of types to show to the respondent (e.g., note,
        multiple-select question). Specifically, `pyxform` assigns more
        concrete subclasses (e.g., `InputQuestion`, `MultipleChoiceQuestion`)
        to survey elements that are "real" questions to display to the
        respondent; and it uses generic `Question` class for elements related
        to internal actions such as calculation.
        """
        from safely_report.survey.form_generator import SurveyFormGenerator

        if isinstance(element, Question) and type(element) is not Question:
            if element.type not in SurveyFormGenerator.FIELD_CLASS:
                raise Exception(f"Unsupported question type: {element.type}")

    @classmethod
    def _check_functions(cls, element: SurveyElement):
        """
        Error out if the given survey element uses unsupported functions.
        """
        from safely_report.survey.survey_processor import SurveyProcessor

        # Extract all logic in current survey element
        logic_string = ""
        logic_string += element.bind.get("relevant", "")
        logic_string += element.bind.get("constraint", "")
        logic_string += element.bind.get("calculate", "")
        logic_string += element.control.get("jr:count", "")

        # Identify all XLSForm functions in current survey element
        function_name_pattern = r"([a-z][a-z\d\:\-]*\()"
        function_name_matches = re.findall(function_name_pattern, logic_string)

        # Validate all XLSForm functions have Python counterparts implemented
        for match in function_name_matches:
            name = match[:-1]  # XLSForm function name
            name_py = "_" + re.sub("[:-]", "_", name)  # Python function name
            if name_py not in dir(SurveyProcessor):
                raise Exception(f"Unsupported XLSForm function: {name}")
