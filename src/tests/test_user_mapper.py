from uuid import uuid4

from datasource.mapper.user_mapper import DatasourceUserMapper
from datasource.model.user import OrmUser
from domain.model.user import DomainUser


def test_user_mapper_domain_to_orm():
    user = DomainUser(uuid4(), "alice", "password-hash")
    result = DatasourceUserMapper.domain_to_orm(user)
    assert isinstance(result, OrmUser)
    assert result.uuid == user.uuid
    assert result.login == user.login
    assert result.password_hash == user.password_hash


def test_user_mapper_orm_to_domain():
    user_uuid = uuid4()
    orm_user = OrmUser(
        uuid=user_uuid, login="alice", password_hash="password-hash"
    )
    result = DatasourceUserMapper.orm_to_domain(orm_user)
    assert isinstance(result, DomainUser)
    assert result == DomainUser(user_uuid, "alice", "password-hash")
