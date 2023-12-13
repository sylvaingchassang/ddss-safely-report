from safely_report.survey.garbling import Garbler, GarblingScheme


def test_parse_xlsform(path_to_xlsform_holidays):
    params = Garbler._parse_xlsform(path_to_xlsform_holidays)
    assert len(params) == 2
    assert params.get("like.travel")
    assert params.get("like.travel").scheme == GarblingScheme.PopBlock
    assert params.get("ever.abroad")
    assert params.get("ever.abroad").scheme == GarblingScheme.IID
