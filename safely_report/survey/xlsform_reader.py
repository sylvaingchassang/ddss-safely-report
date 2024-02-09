from pyxform import Survey
from pyxform.builder import create_survey_element_from_dict
from pyxform.xls2json import parse_file_to_json


class XLSFormReader:
    @staticmethod
    def read_xlsform(path_to_xlsform: str) -> Survey:
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
        survey_tree = create_survey_element_from_dict(survey_dict)

        # TODO: Validate the form
        assert isinstance(survey_tree, Survey)

        return survey_tree
