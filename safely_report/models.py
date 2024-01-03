from csv import DictReader
from typing import Callable, Type

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String

from safely_report.settings import (
    ENUMERATOR_ROSTER_PATH,
    RESPONDENT_ROSTER_PATH,
)
from safely_report.utils import generate_uuid4

db = SQLAlchemy()


class DynamicTable(db.Model):  # type: ignore
    """
    Abstract base class for dynamically defined tables.
    """

    __abstract__ = True

    @staticmethod
    def add_columns_from_csv(path_to_csv: str) -> Callable:
        """
        Return class decorator to define table fields from the given CSV file.
        """

        def decorator(table_cls: Type[DynamicTable]) -> Type[DynamicTable]:
            with open(path_to_csv, "r") as file:
                csv_reader = DictReader(file)
                for name in csv_reader.fieldnames or []:
                    setattr(table_cls, name, Column(String, nullable=True))
            return table_cls

        return decorator

    @classmethod
    def add_data_from_csv(cls, path_to_csv: str):
        """
        Add data from the given CSV file.
        """
        try:
            table_records = []
            with open(path_to_csv, "r") as file:
                csv_reader = DictReader(file)
                for row in csv_reader:
                    table_records.append(cls(**row))
            db.session.add_all(table_records)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


@DynamicTable.add_columns_from_csv(RESPONDENT_ROSTER_PATH)
class Respondent(DynamicTable):
    __tablename__ = "respondents"

    uuid = Column(String(36), primary_key=True, default=generate_uuid4)


@DynamicTable.add_columns_from_csv(ENUMERATOR_ROSTER_PATH)
class Enumerator(DynamicTable):
    __tablename__ = "enumerators"

    uuid = Column(String(36), primary_key=True, default=generate_uuid4)


class SurveyResponse(db.Model):  # type: ignore
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True)
    response = Column(String, nullable=False)  # Stringified JSON

    def __init__(self, response):
        self.response = response

    def __repr__(self):
        return f"<SurveyResponse ID: {self.id}>"


class GarblingBlock(db.Model):  # type: ignore
    __tablename__ = "garbling_blocks"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    shocks = Column(String, nullable=False)  # Stringified array
    version = Column(Integer, nullable=False)

    def __init__(self, name, shocks):
        self.name = name
        self.shocks = shocks

    def __repr__(self):
        return f"<GarblingBlock Name: {self.name}>"

    # For optimistic locking
    __mapper_args__ = {"version_id_col": version}
