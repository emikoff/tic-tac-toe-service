from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from datasource.mapper.user_mapper import DatasourceUserMapper
from datasource.repository.user_repository_implementation import UserRepositoryImpl
from domain.model.user import DomainUser


def make_user(login="alice"):
    return DomainUser(uuid4(), login, "password-hash")


def test_save_and_get_user_by_uuid(clean_database):
    repository = UserRepositoryImpl(DatasourceUserMapper())
    user = make_user()
    repository.save(user)
    assert repository.get_by_uuid(user.uuid) == user


def test_get_user_by_login(clean_database):
    repository = UserRepositoryImpl(DatasourceUserMapper())
    user = make_user("bob")
    repository.save(user)
    assert repository.get_by_login("bob") == user


def test_unknown_user_returns_none(clean_database):
    repository = UserRepositoryImpl(DatasourceUserMapper())
    assert repository.get_by_uuid(uuid4()) is None
    assert repository.get_by_login("unknown") is None


def test_duplicate_login_is_rejected_and_session_recovers(clean_database):
    repository = UserRepositoryImpl(DatasourceUserMapper())
    repository.save(make_user("alice"))
    with pytest.raises(IntegrityError):
        repository.save(make_user("alice"))
    assert repository.get_by_login("alice") is not None
