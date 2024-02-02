import pytest

from safely_report import create_app
from safely_report.models import db


class MockFlaskSession(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = None


@pytest.fixture
def test_db():
    app = create_app()
    with app.app_context():
        # Create tables in the test database
        db.create_all()

        # Yield the database instance for testing
        yield db

        # Clean up and drop tables after testing
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_session():
    return MockFlaskSession()


@pytest.fixture
def path_to_xlsform_holidays():
    return "tests/data/stats4sd_example_xlsform_adapted.xlsx"
