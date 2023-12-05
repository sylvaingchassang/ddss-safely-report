from sqlalchemy import Column, Integer, String

from safely_report import db


class Response(db.Model):  # type: ignore
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True)
    response = Column(String, nullable=False)  # Stringified JSON

    def __init__(self, response):
        self.response = response

    def __repr__(self):
        return f"<Response ID: {self.id}>"
