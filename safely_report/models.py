from csv import DictReader
from typing import Callable, Type

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String

from safely_report.settings import (
    ENUMERATOR_ROSTER_PATH,
    RESPONDENT_ROSTER_PATH,
)

db = SQLAlchemy()


def add_columns_from_csv(path_to_csv: str) -> Callable:
    """
    A class decorator to define table fields from the given CSV file.
    """

    def decorator(cls: Type) -> Type:
        with open(path_to_csv, "r") as file:
            csv_reader = DictReader(file)
            for name in csv_reader.fieldnames or []:
                setattr(cls, name, Column(String, nullable=True))
        return cls

    return decorator


@add_columns_from_csv(RESPONDENT_ROSTER_PATH)
class Respondent(db.Model):  # type: ignore
    __tablename__ = "respondents"

    id = Column(Integer, primary_key=True)


@add_columns_from_csv(ENUMERATOR_ROSTER_PATH)
class Enumerator(db.Model):  # type: ignore
    __tablename__ = "enumerators"

    id = Column(Integer, primary_key=True)


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
