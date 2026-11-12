from datasource.model.user import OrmUser
from domain.model.user import DomainUser


class DatasourceUserMapper:
    @staticmethod
    def orm_to_domain(orm_user: OrmUser) -> DomainUser:
        return DomainUser(
            uuid=orm_user.uuid,
            login=orm_user.login,
            password_hash=orm_user.password_hash,
        )

    @staticmethod
    def domain_to_orm(domain_user: DomainUser) -> OrmUser:
        return OrmUser(
            uuid=domain_user.uuid,
            login=domain_user.login,
            password_hash=domain_user.password_hash,
        )
