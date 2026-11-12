from uuid import UUID as PythonUUID
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped, mapped_column

from datasource.database import db


class OrmUser(db.Model):
    __tablename__ = "users"
    uuid: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    login: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
