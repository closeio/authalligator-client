import contextlib
import datetime

import mock
import pytest

from authalligator_client import exceptions as exc
from authalligator_client.client import Client
from authalligator_client.entities import (
    Account,
    AuthorizeAccountPayload,
    DeleteOtherAccountKeysPayload,
    VerifyAccountPayload,
)
from authalligator_client.enums import AccountErrorCode, ProviderType


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


class TestAuthorizeAccount:
    def test_authorize_account(self, client):
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

    def test_authorize_account_errors(self, client):
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


class TestQueryAccount:
    def test_query_account(self, client):
        expires_at = datetime.datetime.now()
        gql_response = {
            "data": {
                "account": {
                    "__typename": "Account",
                    "provider": "TEST",
                    "username": "test-username",
                    "accessToken": "access-token-example",
                    "accessTokenExpiresAt": expires_at.isoformat(),
                }
            }
        }
        with mock_gql_response(gql_response):
            account = client.query_account(
                provider=ProviderType.TEST,
                username="test-username",
                account_key="example-access-key",
            )

        assert isinstance(account, Account)
        assert account.provider == ProviderType.TEST
        assert account.username == "test-username"
        assert account.access_token == "access-token-example"
        assert account.access_token_expires_at == expires_at

    def test_query_account_errors(self, client):
        gql_response = {
            "data": {
                "account": {
                    "__typename": "AccountError",
                    "code": "TRY_LATER",
                    "message": "dummy-message",
                    "retryIn": 100,
                }
            }
        }
        with mock_gql_response(gql_response):
            with pytest.raises(exc.AccountError) as exc_info:
                client.query_account(
                    provider=ProviderType.TEST,
                    username="test-username",
                    account_key="example-access-key",
                )

        account_error = exc_info.value
        assert account_error.code == AccountErrorCode.TRY_LATER
        assert account_error.message == "dummy-message"
        assert account_error.retry_in == 100


class TestDeleteOtherAccountKeys:
    def test_delete_other_account_keys(self, client):
        gql_response = {
            "data": {
                "deleteOtherAccountKeys": {
                    "__typename": "DeleteOtherAccountKeysPayload",
                }
            }
        }
        with mock_gql_response(gql_response):
            result = client.delete_other_account_keys(
                provider=ProviderType.TEST,
                username="test-username",
                account_key="example-access-key",
            )

        assert isinstance(result, DeleteOtherAccountKeysPayload)

    def test_delete_other_account_keys_errors(self, client):
        gql_response = {
            "data": {
                "deleteOtherAccountKeys": {
                    "__typename": "AccountError",
                    "code": "TRY_LATER",
                    "message": "dummy-message",
                    "retryIn": 100,
                }
            }
        }
        with mock_gql_response(gql_response):
            with pytest.raises(exc.AccountError) as exc_info:
                client.delete_other_account_keys(
                    provider=ProviderType.TEST,
                    username="test-username",
                    account_key="example-access-key",
                )

        account_error = exc_info.value
        assert account_error.code == AccountErrorCode.TRY_LATER
        assert account_error.message == "dummy-message"
        assert account_error.retry_in == 100


class TestVerifyAccount:
    def test_verify_account(self, client):
        expires_at = datetime.datetime.now()
        gql_response = {
            "data": {
                "verifyAccount": {
                    "__typename": "VerifyAccountPayload",
                    "account": {
                        "provider": "TEST",
                        "username": "test-username",
                        "accessToken": "test-access-token",
                        "accessTokenExpiresAt": expires_at.isoformat(),
                    },
                }
            }
        }
        with mock_gql_response(gql_response):
            result = client.verify_account(
                provider=ProviderType.TEST,
                username="test-username",
                account_key="example-access-key",
            )

        assert isinstance(result, VerifyAccountPayload)
        account = result.account
        assert isinstance(account, Account)
        assert account.provider == ProviderType.TEST
        assert account.username == "test-username"
        assert account.access_token == "test-access-token"
        assert account.access_token_expires_at == expires_at

    def test_verify_account_errors(self, client):
        gql_response = {
            "data": {
                "verifyAccount": {
                    "__typename": "AccountError",
                    "code": "TRY_LATER",
                    "message": "dummy-message",
                    "retryIn": 100,
                }
            }
        }
        with mock_gql_response(gql_response):
            with pytest.raises(exc.AccountError) as exc_info:
                client.verify_account(
                    provider=ProviderType.TEST,
                    username="test-username",
                    account_key="example-access-key",
                )

        account_error = exc_info.value
        assert account_error.code == AccountErrorCode.TRY_LATER
        assert account_error.message == "dummy-message"
        assert account_error.retry_in == 100
