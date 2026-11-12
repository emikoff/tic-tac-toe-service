from dataclasses import dataclass
from uuid import UUID


@dataclass
class WebUser:
    uuid: UUID
    login: str
