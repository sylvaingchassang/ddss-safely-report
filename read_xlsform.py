from pyxform import Survey
from pyxform.builder import create_survey_element_from_dict
from pyxform.xls2json import parse_file_to_json


def read_xlsform(path_to_xlsform: str) -> Survey:
    """
    Parse and validate XLSForm to generate its Python representation.
    """
    # Parse the form
    survey_json = parse_file_to_json(
        path=path_to_xlsform,
        default_name="__survey__",
    )
    survey_tree = create_survey_element_from_dict(survey_json)

    # TODO: Validate the form
    assert isinstance(survey_tree, Survey)

    return survey_tree
