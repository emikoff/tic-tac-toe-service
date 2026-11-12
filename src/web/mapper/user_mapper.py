from web.model.user import WebUser
from domain.model.user import DomainUser


class WebUserMapper:
    def domain_to_web(self, domain_user: DomainUser) -> WebUser:
        return WebUser(
            uuid=domain_user.uuid,
            login=domain_user.login,
        )
