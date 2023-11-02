from pyxform import Survey, builder, xls2json


def read_xlsform(path_to_xlsform: str) -> Survey:
    """
    Parse and validate XLSForm to generate its Python representation.
    """
    # Parse the form
    survey_json = xls2json.parse_file_to_json(
        path=path_to_xlsform,
        default_name="__survey__",
    )
    survey_tree = builder.create_survey_element_from_dict(survey_json)

    # TODO: Validate the form
    assert isinstance(survey_tree, Survey)

    return survey_tree
