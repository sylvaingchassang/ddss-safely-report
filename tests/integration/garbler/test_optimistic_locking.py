import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from safely_report.models import (
    GarblingBlock,
    Respondent,
    ResponseStatus,
    SurveyResponse,
)


def test_optimistic_locking(test_db):
    # Pre-populate DB
    block = GarblingBlock(name="test_block", shocks="[True, False]")
    respondent1 = Respondent()
    respondent2 = Respondent()
    test_db.session.add_all([block, respondent1, respondent2])
    test_db.session.commit()

    # Simulate two different DB connections (equivalent to two users)
    Session1 = sessionmaker(bind=test_db.engine)
    Session2 = sessionmaker(bind=test_db.engine)
    session1 = Session1()
    session2 = Session2()

    # Simulate these sessions reading the same block "state" (i.e., version)
    block1 = session1.query(GarblingBlock).filter_by(name="test_block").first()
    block2 = session2.query(GarblingBlock).filter_by(name="test_block").first()
    assert block1.version == block2.version == 1

    # Simulate one session completing its DB transaction first
    block1.shocks = "[True]"
    session1.add(block1)
    response1 = SurveyResponse(
        response="response1",
        respondent_uuid=respondent1.uuid,
    )
    session1.add(response1)
    session1.commit()

    # Simulate the other session completing DB transaction, which should fail
    with pytest.raises(StaleDataError):
        block2.shocks = "[True]"
        session2.add(block2)
        response2 = SurveyResponse(
            response="response2",
            respondent_uuid=respondent2.uuid,
        )
        session2.add(response2)
        session2.commit()

    # Check changes in DB
    test_db.session.refresh(block)
    test_db.session.refresh(respondent1)
    test_db.session.refresh(respondent2)
    assert block.version == 2
    assert respondent1.response_status == ResponseStatus.Complete
    assert respondent2.response_status == ResponseStatus.Incomplete
    assert SurveyResponse.query.count() == 1
    assert SurveyResponse.query.first().respondent_uuid == respondent1.uuid
