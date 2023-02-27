from typing import Any, Dict, List, Optional, Union

from . import enums


class AuthAlligatorException(Exception):
    pass


class UnexpectedStatusCode(AuthAlligatorException):
    """Raised when AuthAlligator returns a non-200 response."""

    def __init__(self, status_code: int, content: Union[str, bytes], *args):
        self.status_code = status_code
        self.content = content
        super(UnexpectedStatusCode, self).__init__(*args)


class AuthAlligatorQueryError(AuthAlligatorException):
    """Raised when an operation results in errors."""

    def __init__(self, errors: List[Dict[str, Any]], *args):
        self.errors = errors
        super(AuthAlligatorQueryError, self).__init__(*args)


class AuthAlligatorUnauthorizedError(UnexpectedStatusCode):
    """Raised specifically for 401 and 403 status codes."""

    pass


class ExecutionResultError(AuthAlligatorException):
    """Raised for the "expected" class of errors, on the schema."""

    pass


class AccountError(ExecutionResultError):
    """Corresponds with the AccountError entity type."""

    def __init__(
        self,
        code: enums.AccountErrorCode,
        message: Optional[str],
        retry_in: Optional[int],
        *args,
    ):
        self.code = code
        self.message = message
        self.retry_in = retry_in
        super(AccountError, self).__init__(*args)
