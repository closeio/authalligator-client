import attr

from . import enums
from .utils import as_json_dict, enum_converter, to_camel_case


@attr.attrs()
class AuthAlligatorInputType(object):
    def as_dict(self):
        serialized = as_json_dict(self)
        # snake_case to camelCase
        return {to_camel_case(k): v for k, v in serialized.items()}


@attr.attrs()
class AuthorizeAccountInput(AuthAlligatorInputType):
    provider = attr.attrib(
        converter=enum_converter(enums.ProviderType)  # type: ignore[misc]
    )  # type: enums.ProviderType
    authorization_code = attr.attrib()  # type: str
    redirect_uri = attr.attrib()  # type: str


@attr.attrs()
class AccountAccessInput(AuthAlligatorInputType):
    provider = attr.attrib(
        converter=enum_converter(enums.ProviderType)  # type: ignore[misc]
    )  # type: enums.ProviderType
    username = attr.attrib()  # type: str
    account_key = attr.attrib()  # type: str
