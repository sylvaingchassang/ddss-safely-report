from pyxform import Survey
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

        # Ensure the form meets requirements specific to our application
        assert isinstance(survey, Survey)
        for element in survey.iter_descendants():
            cls._check_infinite_repeat(element)
            cls._check_nested_repeat(element)

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
