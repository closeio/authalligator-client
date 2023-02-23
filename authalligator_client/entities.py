import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

import attr
import ciso8601
import structlog
from attr import converters

from . import enums
from .utils import as_json_dict, to_snake_case

logger = structlog.get_logger()


class Omitted(Enum):
    """Singleton written in a way mypy can parse.

    See https://www.python.org/dev/peps/pep-0484/#support-for-singleton-types-in-unions
    for more details.
    """

    token = 0


OMITTED = Omitted.token
"""A singleton to differentiate between omitted vs explicit :obj:`None`."""

# helper type for entity_converter
U = TypeVar("U", bound="BaseAAEntity")


def entity_converter(
    entity_cls: Union[List[Type[U]], Type[U]],
) -> Callable[[Union[Omitted, U, Dict]], Union[U, Omitted]]:
    """
    Convert a dictionary response into instances of the entity class.

    Usage:
        # disambiguates between type_a and type_b based on ``__typename``
        converter = entity_converter([TypeA, TypeB])
        my_instance = converter({'__typename': 'TypeB'})

    XXX: mypy isn't expressive enough to annotate that the return type will be
    one of the _specific_ arg types and not the most generic bound base. We'll
    unfortunately have to ``# type: ignore`` on lines that call this.

    Args:
        entity_cls: the class (or classes) the value should be converted into.
            If multiple classes are provided as options, ``__typename`` must be
            included in the reponse to support disambiguation.

    Returns:
        A callable that will convert a dictionary to the right entity type. If
        more than one entity type is possible, that dictionary must have a
        ``__typename`` field present, which must match the ``TYPENAME`` on a
        provided entity. If none of the provided types match of if the fields
        don't align with the provided entity, a ``TypeError`` is raised.
    """
    entity_classes: List[Type[U]] = []
    if isinstance(entity_cls, (list, tuple)):
        entity_classes = entity_cls
    else:
        entity_classes = [entity_cls]

    def _entity_converter(val: Union[Dict[str, Any], U, Omitted]) -> Union[U, Omitted]:
        # check if it's explitly been omitted (don't try to convert those)
        if val is OMITTED:
            return val

        # check if it's already an entity
        if any([isinstance(val, e_cls) for e_cls in entity_classes]):
            return cast(U, val)

        # definitely a dict now, since we check what it was earlier. (present
        # for type checking)
        val = cast(Dict[str, Any], val)

        # if there's more than one possibility for entity classes, pick the
        # right one based on ``__typename``
        if len(entity_classes) == 1:
            # only one option, we don't need an explicit type
            selected_cls: Type[U] = entity_classes[0]
        else:
            # a few different return types are expected
            typename = val.pop("__typename", None)
            if typename is None:
                type_options = ", ".join([e.TYPENAME for e in entity_classes])
                raise TypeError(
                    'No "__typename" present to disambiguate between possible '
                    "types: [{}]".format(type_options)
                )

            matching_typename: Optional[Type[U]] = next(
                (e for e in entity_classes if e.TYPENAME == typename), None
            )
            if matching_typename is None:
                raise TypeError('No entity found for type "{}"'.format(typename))

            selected_cls = matching_typename

        return selected_cls.from_api_response(val)

    return _entity_converter


@attr.attrs(frozen=True)
class BaseAAEntity(object):
    TYPENAME: str = ""
    """The name of the graphql type in the schema.

    Used for disambiguation when there's more than one possible type being
    returned.
    """

    as_dict = as_json_dict

    @classmethod
    def from_api_response(cls: Type[U], data: Dict[str, Any]) -> U:
        # If __typename is present, this asserts that it matches this class's
        # expected typename
        typename = data.pop("__typename", None)
        if typename and typename != cls.TYPENAME:
            raise TypeError(
                (
                    "Given type \"{}\" doesn't match this entity's type: "
                    '"{}". Is {} the right entity for '
                    "this data?"
                ).format(typename, cls.TYPENAME, cls.__name__)
            )

        # convert top-level kwargs from camelCase to snake_case
        kwargs = {to_snake_case(k): v for k, v in data.items()}

        # mypy doesn't like that we're providing kwargs to a type whose init
        # doesn't accept any kwargs (even though subclasses do have attributes)
        return cls(**kwargs)  # type: ignore


@attr.attrs(frozen=True)
class AccountError(BaseAAEntity):
    TYPENAME = "AccountError"

    code: enums.AccountErrorCode = attr.attrib(converter=enums.AccountErrorCode)
    message: Optional[str] = attr.attrib()
    retry_in: Optional[int] = attr.attrib()

@attr.attrs(frozen=True)
class Account(BaseAAEntity):
    TYPENAME = "Account"

    provider: enums.ProviderType = attr.attrib(converter=enums.ProviderType)
    username: str = attr.attrib()
    access_token: Optional[str] = attr.attrib()
    access_token_expires_at: Optional[datetime.datetime] = attr.attrib(
        converter=converters.optional(ciso8601.parse_datetime),
    )


@attr.attrs(frozen=True)
class DeleteOperation(BaseAAEntity):
    """Base class for delete operation payloads.

    These payloads don't actually have any field information in them. While
    there's technically a "_" field in the schema, it's only a placeholder to
    work around the language not supporting empty responses. It has no meaning
    and will never have a meaningful value.

    This class has no specific equivalent type, it's just a convenience type
    for these entities.
    """

    pass


@attr.attrs(frozen=True)
class DeleteOtherAccountKeysPayload(DeleteOperation):
    TYPENAME = "DeleteOtherAccountKeysPayload"


@attr.attrs(frozen=True)
class DeleteAccountKeyPayload(DeleteOperation):
    TYPENAME = "DeleteAccountKeyPayload"


@attr.attrs(frozen=True)
class DeleteAccountPayload(DeleteOperation):
    TYPENAME = "DeleteAccountPayload"


@attr.attrs(frozen=True)
class AuthorizeAccountPayload(BaseAAEntity):
    TYPENAME = "AuthorizeAccountPayload"

    account: Account = attr.attrib(
        converter=entity_converter(Account)  # type: ignore[misc],
    )
    account_key: str = attr.attrib()
    number_of_account_keys: int = attr.attrib()


@attr.attrs(frozen=True)
class VerifyAccountPayload(BaseAAEntity):
    TYPENAME = "VerifyAccountPayload"

    account: Account = attr.attrib(
        converter=entity_converter(Account),  # type: ignore[misc]
    )


@attr.attrs(frozen=True)
class Query(BaseAAEntity):
    account: Union[Omitted, Account, AccountError] = attr.attrib(
        default=OMITTED,
        converter=entity_converter([Account, AccountError])  # type: ignore[misc]
    )


@attr.attrs(frozen=True)
class Mutation(BaseAAEntity):
    # mypy and the attrs plugin doens't like the `Omitted` default + converter
    # stuff
    authorize_account: Union[Omitted, AuthorizeAccountPayload, AccountError] = attr.attrib(  # type: ignore
        default=OMITTED,
        # ignore unsupport converter warning
        converter=cast(  # type: ignore[misc]
            Union[Omitted, AuthorizeAccountPayload, AccountError],
            entity_converter([AuthorizeAccountPayload, AccountError]),
        ),
    )
    verify_account: Union[Omitted, VerifyAccountPayload, AccountError] = attr.attrib(  # type: ignore
        default=OMITTED,
        converter=cast(  # type: ignore[misc]
            Union[Omitted, VerifyAccountPayload, AccountError],
            entity_converter([VerifyAccountPayload, AccountError]),
        ),
    )
    delete_account: Union[Omitted, DeleteAccountPayload, AccountError] = attr.attrib(  # type: ignore
        default=OMITTED,
        converter=cast(  # type: ignore[misc]
            Union[Omitted, DeleteAccountPayload, AccountError],
            entity_converter([DeleteAccountPayload, AccountError]),
        ),
    )
    delete_account_key: Union[Omitted, DeleteAccountKeyPayload, AccountError] = attr.attrib(  # type: ignore
        default=OMITTED,
        converter=cast(  # type: ignore[misc]
            Union[Omitted, DeleteAccountKeyPayload, AccountError],
            entity_converter([DeleteAccountKeyPayload, AccountError]),
        ),
    )
    delete_other_account_keys: Union[Omitted, DeleteOtherAccountKeysPayload, AccountError] = attr.attrib(  # type: ignore
        default=OMITTED,
        # ignore unsupport converter warning
        converter=cast(  # type: ignore[misc]
            Union[Omitted, DeleteOtherAccountKeysPayload, AccountError],
            entity_converter([DeleteOtherAccountKeysPayload, AccountError]),
        ),
    )
