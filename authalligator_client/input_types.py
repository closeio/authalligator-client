import attr

from . import enums
from .utils import as_json_dict, enum_converter, to_camel_case


@attr.attrs(auto_attribs=True)
class AuthAlligatorInputType:
    def as_dict(self):
        serialized = as_json_dict(self)
        # snake_case to camelCase
        return {to_camel_case(k): v for k, v in serialized.items()}


@attr.attrs(auto_attribs=True)
class AuthorizeAccountInput(AuthAlligatorInputType):
    provider: enums.ProviderType = attr.attrib(
        converter=enum_converter(enums.ProviderType)  # type: ignore[misc]
    )
    authorization_code: str
    redirect_uri: str


@attr.attrs(auto_attribs=True)
class AccountAccessInput(AuthAlligatorInputType):
    provider: enums.ProviderType = attr.attrib(
        converter=enum_converter(enums.ProviderType)  # type: ignore[misc]
    )
    username: str
    account_key: str
