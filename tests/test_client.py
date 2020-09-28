import datetime
import contextlib
import pytest
import mock

from authalligator_client.client import Client
from authalligator_client.enums import ProviderType, AccountErrorCode
from authalligator_client.entities import AuthorizeAccountPayload, Account
from authalligator_client import exceptions as exc


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


@contextlib.contextmanager
def mock_gql_response(json_data, status_code=200):
    """Shortcut for mocking a reponse."""
    with mock.patch("authalligator_client.client.requests.post") as mock_post:
        mock_post.return_value = MockResponse(
            json_data=json_data, status_code=status_code
        )
        yield mock_post


@pytest.fixture
def client():
    return Client(token="dummy", service_url="example.com")


def test_authorize_account(client):
    expires_at = datetime.datetime.now()
    gql_response = {
        "data": {
            "authorizeAccount": {
                "__typename": "AuthorizeAccountPayload",
                "account": {
                    "provider": "TEST",
                    "username": "test-username",
                    "accessToken": "access-token-example",
                    "accessTokenExpiresAt": expires_at.isoformat(),
                },
                "accountKey": "dummy-account-key",
                "numberOfAccountKeys": 1,
            }
        }
    }
    with mock_gql_response(gql_response):
        authorize_account = client.authorize_account(
            provider=ProviderType.TEST,
            authorization_code="example-auth-code",
            redirect_uri="example.com/oauth/redirect",
        )

    assert isinstance(authorize_account, AuthorizeAccountPayload)
    assert authorize_account.account_key == "dummy-account-key"
    assert authorize_account.number_of_account_keys == 1

    account = authorize_account.account
    assert isinstance(account, Account)
    assert account.provider == ProviderType.TEST
    assert account.username == "test-username"
    assert account.access_token == "access-token-example"
    assert account.access_token_expires_at == expires_at


def test_authorize_account_errors(client):
    gql_response = {
        "data": {
            "authorizeAccount": {
                "__typename": "AccountError",
                "code": "TRY_LATER",
                "message": "dummy-message",
                "retryIn": 100,
            }
        }
    }
    with mock_gql_response(gql_response):
        with pytest.raises(exc.AccountError) as exc_info:
            client.authorize_account(
                provider=ProviderType.TEST,
                authorization_code="example-auth-code",
                redirect_uri="example.com/oauth/redirect",
            )

    account_error = exc_info.value
    assert account_error.code == AccountErrorCode.TRY_LATER
    assert account_error.message == "dummy-message"
    assert account_error.retry_in == 100
