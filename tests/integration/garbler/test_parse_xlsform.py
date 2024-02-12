import tempfile

import openpyxl
import pytest

from safely_report.survey.garbling import Garbler, GarblingScheme


def test_parse_xlsform(path_to_xlsform_holidays):
    params = Garbler._parse_xlsform(path_to_xlsform_holidays)
    assert len(params) == 2
    assert params.get("like.travel")
    assert params.get("like.travel").scheme == GarblingScheme.PopBlock
    assert params.get("ever.abroad")
    assert params.get("ever.abroad").scheme == GarblingScheme.IID


def test_xlsform_validation(path_to_xlsform_test_cases):
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as temp_file:
        workbook = openpyxl.load_workbook(path_to_xlsform_test_cases)
        sheet = workbook["garbling_in_repeat"]
        sheet.title = "survey"
        workbook.save(temp_file.name)

        with pytest.raises(Exception) as e:
            Garbler._parse_xlsform(temp_file.name)
        assert str(e.value) == "Garbling should not be applied inside repeats"
