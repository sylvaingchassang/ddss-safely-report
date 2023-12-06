import pytest

from safely_report.survey.garbling import Garbler


@pytest.fixture
def survey_dict():
    return {
        "type": "survey",
        "children": [
            {
                "type": "select one",
            },
            {
                "type": "select one",
                "garbling": {"rate": "0.3", "answer": "yes"},
            },
            {
                "type": "repeat",
                "children": [
                    {
                        "type": "select one",
                    },
                    {
                        "type": "select one",
                        "garbling": {"rate": "0.5", "answer": "yes"},
                    },
                ],
            },
        ],
    }


def test_find_elements_with_garbling_including_repeats(survey_dict):
    lst = Garbler._find_elements_with_garbling(survey_dict)
    assert len(lst) == 2


def test_find_elements_with_garbling_excluding_repeats(survey_dict):
    lst = Garbler._find_elements_with_garbling(survey_dict, skip_repeat=True)
    assert len(lst) == 1
