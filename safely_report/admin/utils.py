from safely_report.models import SurveyResponse
from safely_report.utils import deserialize


def gather_all_responses_to_csv() -> str:
    """
    Arrange all submitted survey responses into a CSV string.

    Returns
    -------
    str
        A CSV string containing submitted response data
        (an empty string if no response exists yet)
    """
    RESPONDENT_UUID = SurveyResponse.respondent_uuid.name
    ENUMERATOR_UUID = SurveyResponse.enumerator_uuid.name

    # Retrieve all submitted survey responses
    survey_responses = SurveyResponse.query.all()
    if len(survey_responses) == 0:
        return ""

    # Extract response data
    column_names: set[str] = set()
    responses: list[dict] = []
    for surv_resp in survey_responses:
        assert isinstance(surv_resp, SurveyResponse)
        resp = deserialize(str(surv_resp.response))

        assert isinstance(resp, dict)
        resp[RESPONDENT_UUID] = surv_resp.respondent_uuid
        resp[ENUMERATOR_UUID] = surv_resp.enumerator_uuid

        responses.append(resp)

        column_names.update(resp.keys())

    # Sort column names
    column_names.remove(RESPONDENT_UUID)
    column_names.remove(ENUMERATOR_UUID)
    column_names_sorted = [RESPONDENT_UUID, ENUMERATOR_UUID]
    column_names_sorted += sorted(column_names)

    # Construct a single CSV string
    csv_string = ",".join(column_names_sorted) + "\n"  # Header
    for resp in responses:
        row_string = [str(resp.get(name, "")) for name in column_names_sorted]
        csv_string += ",".join(row_string) + "\n"

    return csv_string
