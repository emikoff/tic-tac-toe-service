from dataclasses import dataclass
from uuid import UUID


@dataclass
class DomainUser:
    uuid: UUID
    login: str
    password_hash: str
