from typing import Any, Dict, List


class AuthAlligatorException(Exception):
    pass


class UnexpectedStatusCode(AuthAlligatorException):
    """Raised when AuthAlligator returns a non-200 response."""

    status_code: int
    content: str

    def __init__(self, status_code, content, *args, **kwargs):
        self.status_code = status_code
        self.content = content
        super().__init__(*args, **kwargs)


class AuthAlligatorQueryError(AuthAlligatorException):
    """Raised when an operation results in errors."""

    errors: List[Dict[str, Any]]

    def __init__(self, errors, *args, **kwargs):
        self.errors = errors
        super().__init__(*args, **kwargs)


class AuthAlligatorUnauthorizedError(UnexpectedStatusCode):
    """Raised specifically for 401 and 403 status codes."""
