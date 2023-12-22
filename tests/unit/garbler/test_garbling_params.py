import pytest

from safely_report.survey.garbling import (
    Garbler,
    GarblingParams,
    GarblingScheme,
)


@pytest.fixture
def survey_dict_record():
    return {
        "name": "ever.abroad",
        "choices": [
            {"label": {"English": "Yes"}, "name": "yes"},
            {"label": {"English": "No"}, "name": "no"},
        ],
    }


@pytest.mark.parametrize(
    "garbling_covariate, garbling_scheme_expected",
    [
        (None, GarblingScheme.IID),
        ("", GarblingScheme.IID),
        ("*", GarblingScheme.PopBlock),
        ("married", GarblingScheme.CovBlock),
    ],
)
def test_garbling_scheme(garbling_covariate, garbling_scheme_expected):
    garbling_params = GarblingParams(
        question="question",
        answer="yes",
        rate=0.3,
        covariate=garbling_covariate,
    )
    assert garbling_params.scheme == garbling_scheme_expected


@pytest.mark.parametrize(
    "garbling_dict, garbling_answer, garbling_rate, garbling_covariate, garbling_scheme",
    [
        (
            {"rate": "0.3", "answer": "yes"},
            "yes",
            0.3,
            None,
            GarblingScheme.IID,
        ),
        (
            {"rate": "0.5", "answer": "yes", "covariate": "*"},
            "yes",
            0.5,
            "*",
            GarblingScheme.PopBlock,
        ),
        (
            {"rate": "0.75", "answer": "yes", "covariate": "married"},
            "yes",
            0.75,
            "married",
            GarblingScheme.CovBlock,
        ),
    ],
)
def test_extract_garbling_params(
    # Fixture(s)
    survey_dict_record,
    # Parameter(s)
    garbling_dict,
    garbling_answer,
    garbling_rate,
    garbling_covariate,
    garbling_scheme,
):
    survey_dict_record["garbling"] = garbling_dict
    garbling_params = Garbler._extract_garbling_params(survey_dict_record)
    assert garbling_params.question == "ever.abroad"
    assert garbling_params.answer == garbling_answer
    assert garbling_params.rate == garbling_rate
    assert garbling_params.covariate == garbling_covariate
    assert garbling_params.scheme == garbling_scheme


def test_extract_garbling_params_nonexistent(survey_dict_record):
    with pytest.raises(KeyError):
        Garbler._extract_garbling_params(survey_dict_record)


@pytest.mark.parametrize(
    "garbling_dict",
    [
        {"rate-typo": "0.3", "answer": "yes"},
        {"rate": "0.3", "answer-typo": "yes"},
    ],
)
def test_extract_garbling_params_with_missing_fields(
    # Fixture(s)
    survey_dict_record,
    # Parameter(s)
    garbling_dict,
):
    survey_dict_record["garbling"] = garbling_dict
    with pytest.raises(KeyError):
        Garbler._extract_garbling_params(survey_dict_record)


@pytest.mark.parametrize(
    "garbling_dict",
    [
        {"rate": "-0.1", "answer": "yes"},
        {"rate": "1.1", "answer": "yes"},
    ],
)
def test_extract_garbling_params_with_rate_out_of_range(
    # Fixture(s)
    survey_dict_record,
    # Parameter(s)
    garbling_dict,
):
    survey_dict_record["garbling"] = garbling_dict
    with pytest.raises(ValueError) as e:
        Garbler._extract_garbling_params(survey_dict_record)
        assert e.value == "Garbling rate should be between 0 and 1"


@pytest.mark.parametrize(
    "garbling_dict",
    [
        {"rate": "0.3", "answer": "yes", "covariate": "*"},
        {"rate": "0.7", "answer": "yes", "covariate": "*"},
    ],
)
def test_extract_garbling_params_with_unsupported_rate_in_block_garbling(
    # Fixture(s)
    survey_dict_record,
    # Parameter(s)
    garbling_dict,
):
    survey_dict_record["garbling"] = garbling_dict
    with pytest.raises(Exception) as e:
        Garbler._extract_garbling_params(survey_dict_record)
        assert e.value == "Block garbling supports the following rates only: "
        "[0.2, 0.25, 0.4, 0.5, 0.6, 0.75, 0.8]"


def test_extract_garbling_params_with_answer_not_in_choices(
    survey_dict_record,
):
    survey_dict_record["garbling"] = {"rate": "0.3", "answer": "male"}
    with pytest.raises(Exception) as e:
        Garbler._extract_garbling_params(survey_dict_record)
        assert e.value == "male not in choice options for ever.abroad"
