import attr

from . import enums
from .utils import as_json_dict, to_camel_case


@attr.attrs()
class AuthAlligatorInputType(object):
    def as_dict(self):
        serialized = as_json_dict(self)
        # snake_case to camelCase
        return {to_camel_case(k): v for k, v in serialized.items()}


@attr.attrs()
class AuthorizeAccountInput(AuthAlligatorInputType):
    provider: enums.ProviderType = attr.attrib(converter=enums.ProviderType)
    authorization_code: str = attr.attrib()
    redirect_uri: str = attr.attrib()


@attr.attrs()
class AccountAccessInput(AuthAlligatorInputType):
    provider: enums.ProviderType = attr.attrib(converter=enums.ProviderType)
    username: str = attr.attrib()
    account_key: str = attr.attrib()


@attr.attrs()
class DeleteAccountInput(AuthAlligatorInputType):
    provider: enums.ProviderType = attr.attrib(converter=enums.ProviderType)
    username: str = attr.attrib()
