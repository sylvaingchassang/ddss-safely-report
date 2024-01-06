import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from safely_report.models import GarblingBlock, SurveyResponse
from safely_report.utils import generate_uuid4


def test_optimistic_locking(test_db):
    # Pre-populate DB
    block = GarblingBlock(name="test_block", shocks="[True, False]")
    test_db.session.add(block)
    test_db.session.commit()

    # Simulate two different DB connections (equivalent to two users)
    Session1 = sessionmaker(bind=test_db.engine)
    Session2 = sessionmaker(bind=test_db.engine)
    session1 = Session1()
    session2 = Session2()
    uuid1 = generate_uuid4()
    uuid2 = generate_uuid4()

    # Simulate these sessions reading the same block "state" (i.e., version)
    block1 = session1.query(GarblingBlock).filter_by(name="test_block").first()
    block2 = session2.query(GarblingBlock).filter_by(name="test_block").first()
    assert block1.version == block2.version == 1

    # Simulate one session completing its DB transaction first
    block1.shocks = "[True]"
    session1.add(block1)
    response1 = SurveyResponse(response="response1", respondent_uuid=uuid1)
    session1.add(response1)
    session1.commit()

    # Simulate the other session completing DB transaction, which should fail
    with pytest.raises(StaleDataError):
        block2.shocks = "[True]"
        session2.add(block2)
        response2 = SurveyResponse(response="response2", respondent_uuid=uuid2)
        session2.add(response2)
        session2.commit()

    # Check changes in DB
    block_updated = GarblingBlock.query.filter_by(name="test_block").first()
    assert block_updated.version == 2
    assert SurveyResponse.query.count() == 1
    assert SurveyResponse.query.first().response == "response1"
