from enum import Enum


class AccountErrorCode(Enum):
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DOES_NOT_EXIST = "DOES_NOT_EXIST"
    LOCK_ERROR = "LOCK_ERROR"
    PROVIDER_CONNECTION_ERROR = "PROVIDER_CONNECTION_ERROR"
    TRY_LATER = "TRY_LATER"


class ProviderType(Enum):
    TEST = "TEST"
    GOOGLE = "GOOGLE"
    ZOOM = "ZOOM"
    MICROSOFT = "MICROSOFT"
    CALENDLY = "CALENDLY"
