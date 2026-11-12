from uuid import UUID

from sqlalchemy import select

from domain.model.user import DomainUser
from datasource.repository.user_repository import UserRepository
from datasource.mapper.user_mapper import DatasourceUserMapper
from datasource.model.user import OrmUser

from datasource.database import db


class UserRepositoryImpl(UserRepository):
    def __init__(self, user_mapper: DatasourceUserMapper):
        self.user_mapper = user_mapper

    def save(self, user: DomainUser) -> None:
        try:
            orm_user = self.user_mapper.domain_to_orm(user)
            db.session.add(orm_user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def get_by_login(self, login: str) -> DomainUser | None:
        statement = select(OrmUser).where(OrmUser.login == login)
        orm_user = db.session.execute(statement).scalar_one_or_none()

        if orm_user is None:
            return None
        return self.user_mapper.orm_to_domain(orm_user)

    def get_by_uuid(self, user_uuid: UUID) -> DomainUser | None:
        orm_user = db.session.get(OrmUser, user_uuid)

        if orm_user is None:
            return None

        return self.user_mapper.orm_to_domain(orm_user)
