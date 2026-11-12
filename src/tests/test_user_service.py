from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from datasource.repository.user_repository import UserRepository
from domain.exception.user_exception import UserAlreadyExistsError
from domain.model.user import DomainUser
from domain.service.user_implementation_service import UserServiceImpl


@pytest.fixture
def repository():
    return Mock(spec=UserRepository)


@pytest.fixture
def service(repository):
    return UserServiceImpl(repository)


def test_create_user_generates_uuid_and_saves(service, repository):
    repository.get_by_login.return_value = None
    result = service.create_user("alice", "password-hash")
    assert isinstance(result.uuid, UUID)
    assert result.login == "alice"
    assert result.password_hash == "password-hash"
    repository.save.assert_called_once_with(result)


def test_create_user_rejects_existing_login(service, repository):
    repository.get_by_login.return_value = DomainUser(
        uuid4(), "alice", "existing-hash"
    )
    with pytest.raises(UserAlreadyExistsError):
        service.create_user("alice", "new-hash")
    repository.save.assert_not_called()


def test_get_by_login_delegates_to_repository(service, repository):
    expected = DomainUser(uuid4(), "alice", "password-hash")
    repository.get_by_login.return_value = expected
    assert service.get_by_login("alice") is expected
    repository.get_by_login.assert_called_once_with(login="alice")


def test_get_by_uuid_delegates_to_repository(service, repository):
    user_uuid = uuid4()
    expected = DomainUser(user_uuid, "alice", "password-hash")
    repository.get_by_uuid.return_value = expected
    assert service.get_by_uuid(user_uuid) is expected
    repository.get_by_uuid.assert_called_once_with(user_uuid=user_uuid)
