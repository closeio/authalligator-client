from typing import Any, Dict, List, Union


class AuthAlligatorException(Exception):
    pass


class UnexpectedStatusCode(AuthAlligatorException):
    """Raised when AuthAlligator returns a non-200 response."""

    def __init__(self, status_code, content, *args):
        # type: (int, Union[str, bytes], *Any) -> None
        self.status_code = status_code
        self.content = content
        super().__init__(*args)


class AuthAlligatorQueryError(AuthAlligatorException):
    """Raised when an operation results in errors."""

    def __init__(self, errors, *args):
        # type: (List[Dict[str, Any]], *Any) -> None
        self.errors = errors
        super().__init__(*args)


class AuthAlligatorUnauthorizedError(UnexpectedStatusCode):
    """Raised specifically for 401 and 403 status codes."""
