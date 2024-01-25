import enum
from csv import DictReader
from typing import Callable, Optional, Type, Union

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    delete,
    event,
    insert,
    update,
)
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper, relationship

from safely_report.settings import (
    ENUMERATOR_ROSTER_PATH,
    RESPONDENT_ROSTER_PATH,
)
from safely_report.utils import deserialize, generate_uuid4

db = SQLAlchemy()


class BaseTable(db.Model):  # type: ignore
    """
    Abstract base class for all tables.
    """

    __abstract__ = True

    @classmethod
    def to_csv_string(cls) -> str:
        """
        Arrange all data into a CSV string.
        """
        table_records = cls.query.all()
        column_names = [column.name for column in cls.__table__.columns]
        csv_string = ",".join(column_names) + "\n"  # Header
        for record in table_records:
            row = [getattr(record, name) for name in column_names]
            row_string = [str(val) if val else "" for val in row]
            csv_string += ",".join(row_string) + "\n"

        return csv_string


class DynamicTable(BaseTable):
    """
    Abstract class for dynamically defined tables.
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


class SurveyStatus(enum.Enum):
    Complete = "Complete"
    Incomplete = "Incomplete"


@DynamicTable.add_columns_from_csv(RESPONDENT_ROSTER_PATH)
class Respondent(DynamicTable):
    __tablename__ = "respondents"

    id = Column(Integer, primary_key=True)
    uuid = Column(
        String(36),
        nullable=False,
        unique=True,
        default=generate_uuid4,
    )
    survey_status = Column(
        Enum(SurveyStatus),  # type: ignore
        nullable=False,
        default=SurveyStatus.Incomplete,
    )

    # Respondent may complete the survey with an enumerator
    enumerator_uuid = Column(String(36), ForeignKey("enumerators.uuid"))
    enumerator = relationship("Enumerator")

    @classmethod
    def pre_populate(cls):
        if cls.query.first() is None:
            cls.add_data_from_csv(RESPONDENT_ROSTER_PATH)


@DynamicTable.add_columns_from_csv(ENUMERATOR_ROSTER_PATH)
class Enumerator(DynamicTable):
    __tablename__ = "enumerators"

    id = Column(Integer, primary_key=True)
    uuid = Column(
        String(36),
        nullable=False,
        unique=True,
        default=generate_uuid4,
    )

    @classmethod
    def pre_populate(cls):
        if cls.query.first() is None:
            cls.add_data_from_csv(ENUMERATOR_ROSTER_PATH)


class Role(enum.Enum):
    Respondent = "Respondent"
    Enumerator = "Enumerator"
    Admin = "Admin"


class User(BaseTable, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False, unique=True)
    role = Column(Enum(Role), nullable=False)  # type: ignore

    @classmethod
    def init_admin(cls):
        if cls._get_admin() is None:
            cls._init_admin()

    @classmethod
    def get_admin(cls) -> "User":
        user = cls._get_admin()
        if user is None:
            cls._init_admin()
            user = cls._get_admin()
        assert isinstance(user, User)  # For type check to work
        return user

    @classmethod
    def _init_admin(cls):
        try:
            user = cls(uuid=generate_uuid4(), role=Role.Admin)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def _get_admin(cls) -> Optional["User"]:
        return cls.query.filter_by(role=Role.Admin).first()


@event.listens_for(Respondent, "after_insert")
@event.listens_for(Enumerator, "after_insert")
def create_user(
    mapper: Mapper,
    connection: Connection,
    target: Union[Respondent, Enumerator],
):
    """
    Create a user record for every new respondent or enumerator.
    """
    if isinstance(target, Respondent):
        role = Role.Respondent
    elif isinstance(target, Enumerator):
        role = Role.Enumerator
    connection.execute(insert(User).values(uuid=target.uuid, role=role))


@event.listens_for(Respondent, "after_delete")
@event.listens_for(Enumerator, "after_delete")
def delete_user(
    mapper: Mapper,
    connection: Connection,
    target: Union[Respondent, Enumerator],
):
    """
    Delete the user record of any removed respondent or enumerator.
    """
    connection.execute(delete(User).where(User.uuid == target.uuid))


class SurveyResponse(BaseTable):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True)
    response = Column(String, nullable=False)  # Stringified JSON
    respondent_uuid = Column(
        String(36),
        ForeignKey("respondents.uuid"),
        nullable=False,
        unique=True,  # Restrict respondents to a single response
    )
    enumerator_uuid = Column(
        String(36),
        ForeignKey("enumerators.uuid"),
        nullable=True,
        unique=False,  # Same enumerator can help multiple respondents
    )

    def __init__(self, response, respondent_uuid, enumerator_uuid=None):
        self.response = response
        self.respondent_uuid = respondent_uuid
        self.enumerator_uuid = enumerator_uuid

    @classmethod
    def to_csv_string(cls) -> str:
        """
        Arrange all data into a CSV string.
        """
        RESPONDENT_UUID = cls.respondent_uuid.name
        ENUMERATOR_UUID = cls.enumerator_uuid.name

        # Retrieve all submitted survey responses
        survey_responses = cls.query.all()

        # Extract response data
        variable_names: set[str] = set()
        responses: list[dict] = []
        for surv_resp in survey_responses:
            assert isinstance(surv_resp, cls)
            resp = deserialize(str(surv_resp.response))

            assert isinstance(resp, dict)
            resp[RESPONDENT_UUID] = surv_resp.respondent_uuid
            resp[ENUMERATOR_UUID] = surv_resp.enumerator_uuid

            responses.append(resp)

            variable_names.update(resp.keys())

        # Sort column names
        column_names = sorted(variable_names)
        column_names.remove(RESPONDENT_UUID)
        column_names.remove(ENUMERATOR_UUID)
        column_names[:0] = [RESPONDENT_UUID, ENUMERATOR_UUID]  # Prepend

        # Construct a single CSV string
        csv_string = ",".join(column_names) + "\n"  # Header
        for resp in responses:
            row_string = [str(resp.get(name, "")) for name in column_names]
            csv_string += ",".join(row_string) + "\n"

        return csv_string


@event.listens_for(SurveyResponse, "after_insert")
def update_respondent_info(
    mapper: Mapper,
    connection: Connection,
    target: SurveyResponse,
):
    """
    Update respondent information when their response is submitted.
    """
    connection.execute(
        update(Respondent)
        .where(Respondent.uuid == target.respondent_uuid)
        .values(
            survey_status=SurveyStatus.Complete,
            enumerator_uuid=target.enumerator_uuid,
        )
    )


class GarblingBlock(BaseTable):
    __tablename__ = "garbling_blocks"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    shocks = Column(String, nullable=False)  # Stringified array
    version = Column(Integer, nullable=False)

    def __init__(self, name, shocks):
        self.name = name
        self.shocks = shocks

    # For optimistic locking
    __mapper_args__ = {"version_id_col": version}
