from __future__ import unicode_literals

from typing import Any, Dict, List, Optional, Type, TypeVar

import attr
import requests
import structlog

from . import entities, enums, exceptions as exc, input_types
from .utils import retry

logger = structlog.get_logger()

# helper for typing _make_request
T = TypeVar("T", bound=entities.BaseAAEntity)


@attr.attrs
class Client(object):
    token: str = attr.attrib()
    service_url: str = attr.attrib()

    timeout: int = attr.attrib(default=10)

    @retry(exc=requests.exceptions.RequestException, tries=3, wait=1)
    def _make_request(
        self,
        query: str,
        variables: Dict[str, Any],
        return_types: Type[T],
    ) -> T:
        response = requests.post(
            "{}/graphql".format(self.service_url),
            json={"query": query, "variables": variables},
            auth=(self.token, ""),
            timeout=self.timeout,
        )

        # responses (even for errors) should always be HTTP 200
        if response.status_code != 200:
            if response.status_code in (401, 403):
                exc_cls: Type[
                    exc.UnexpectedStatusCode
                ] = exc.AuthAlligatorUnauthorizedError
            else:
                exc_cls = exc.UnexpectedStatusCode

            raise exc_cls(status_code=response.status_code, content=response.content)

        result = response.json()

        # errors are also unexpected
        errors = result.get("errors")
        if errors:
            raise exc.AuthAlligatorQueryError(errors=errors)

        data = result["data"]
        converted_result = entities.entity_converter(return_types)(data)

        # this should never happen
        assert converted_result is not entities.OMITTED

        return converted_result

    def authorize_account(
        self,
        provider: enums.ProviderType,
        authorization_code: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
    ) -> entities.AuthorizeAccountPayload:
        """Obtain OAuth access token and refresh token.

        This does some basic error handling on the reponse.

        Args:
            provider: the provider to authorize an account for. This must match
                one of the enums.ProviderType values.
            authorization_code: the code present in the callback
            redirect_uri: the redirect uri expected, sent with the oauth
                request for a token

        Returns:
            Either an AuthorizeAccountPayload, or an AccountError if an
            AuthAlligator-handled error was encountered.
        """
        query = """
            mutation authorizeAccount($input: AuthorizeAccountInput!) {
              authorizeAccount(input: $input) {
                __typename
                ... on AuthorizeAccountPayload {
                  account {
                    provider
                    username
                    accessToken
                    accessTokenExpiresAt
                  }
                  accountKey
                  numberOfAccountKeys
                }
                ... on AccountError {
                  code
                  message
                  retryIn
                }
              }
            }
        """

        input_var = input_types.AuthorizeAccountInput(
            provider=provider,
            authorization_code=authorization_code,
            redirect_uri=redirect_uri,
        )
        result = self._make_request(
            query=query,
            variables={"input": input_var.as_dict()},
            return_types=entities.Mutation,
        )
        assert result.authorize_account is not entities.OMITTED
        if isinstance(result.authorize_account, entities.AccountError):
            raise exc.AccountError(
                code=result.authorize_account.code,
                message=result.authorize_account.message,
                retry_in=result.authorize_account.retry_in,
            )

        return result.authorize_account

    def query_account(
        self,
        provider: enums.ProviderType,
        username: str,
        account_key: str,
        scopes: Optional[List[str]] = None,
    ) -> entities.Account:
        """Obtain a valid access token.

        Args:
            provider: the AuthAlligator provider this account is for. (should
                be one of the ``ProviderType`` enum values)
            username: the AuthAlligator-provided username for the account (this
                will likely _not_ be the human-legible email/username)
            account_key: the AuthAlligator-specific secret key that proves we
                have access to the specific account
            scopes: a list of scopes to request for the access token

        Returns:
            The access token and expiration time for said access token.
        """
        query = """
            query getAccount($access: AccountAccessInput!, $scopes: [String!]) {
              account(access: $access, scopes: $scopes) {
                __typename
                ... on Account {
                  provider
                  username
                  accessToken
                  accessTokenExpiresAt
                }
                ... on AccountError {
                  code
                  message
                  retryIn
                }
              }
            }
        """
        input_var = input_types.AccountAccessInput(
            provider=provider,
            username=username,
            account_key=account_key,
        )
        result = self._make_request(
            query=query,
            variables={"access": input_var.as_dict(), "scopes": scopes},
            return_types=entities.Query,
        )
        assert result.account is not entities.OMITTED
        if isinstance(result.account, entities.AccountError):
            raise exc.AccountError(
                code=result.account.code,
                message=result.account.message,
                retry_in=result.account.retry_in,
            )
        return result.account

    def delete_other_account_keys(
        self,
        provider: enums.ProviderType,
        username: str,
        account_key: str,
    ) -> entities.DeleteOtherAccountKeysPayload:
        """Delete other account keys which have access to this account.

        Args:
            provider: the AuthAlligator provider this account is for. (should
                be one of the ``ProviderType`` enum values)
            username: the AuthAlligator-provided username for the account (this
                will likely _not_ be the human-legible email/username)
            account_key: the AuthAlligator-specific secret key that proves we
                have access to the specific account

        Returns:
            DeleteOtherAccountKeysPayload on success.

        Raises:
            AccountError in case of an account error.
        """
        query = """
            mutation deleteOtherAccountKeys($input: AccountAccessInput!) {
              deleteOtherAccountKeys(input: $input) {
                __typename
                ... on AccountError {
                  code
                  message
                  retryIn
                }
              }
            }
        """
        input_var = input_types.AccountAccessInput(
            provider=provider,
            username=username,
            account_key=account_key,
        )
        result = self._make_request(
            query=query,
            variables={"input": input_var.as_dict()},
            return_types=entities.Mutation,
        )

        delete_keys = result.delete_other_account_keys
        assert delete_keys is not entities.OMITTED
        if isinstance(delete_keys, entities.AccountError):
            raise exc.AccountError(
                code=delete_keys.code,
                message=delete_keys.message,
                retry_in=delete_keys.retry_in,
            )
        return delete_keys

    def verify_account(
        self,
        provider: enums.ProviderType,
        username: str,
        account_key: str,
    ) -> entities.VerifyAccountPayload:
        """Verify that the current access token works, and refresh if needed.

        Args:
            provider: the AuthAlligator provider this account is for. (should
                be one of the ``ProviderType`` enum values)
            username: the AuthAlligator-provided username for the account (this
                will likely _not_ be the human-legible email/username)
            account_key: the AuthAlligator-specific secret key that proves we
                have access to the specific account

        Returns:
            VerifyAccountPayload on success.

        Raises:
            AccountError in case of an account error.
        """
        query = """
            mutation verifyAccount($input: AccountAccessInput!) {
              verifyAccount(input: $input) {
                __typename
                ... on VerifyAccountPayload {
                    account {
                        provider
                        username
                        accessToken
                        accessTokenExpiresAt
                    }
                }
                ... on AccountError {
                  code
                  message
                  retryIn
                }
              }
            }
        """
        input_var = input_types.AccountAccessInput(
            provider=provider,
            username=username,
            account_key=account_key,
        )
        result = self._make_request(
            query=query,
            variables={"input": input_var.as_dict()},
            return_types=entities.Mutation,
        )

        verify_account = result.verify_account
        assert verify_account is not entities.OMITTED
        if isinstance(verify_account, entities.AccountError):
            raise exc.AccountError(
                code=verify_account.code,
                message=verify_account.message,
                retry_in=verify_account.retry_in,
            )
        return verify_account

    def delete_account_key(
        self,
        provider: enums.ProviderType,
        username: str,
        account_key: str,
    ) -> entities.DeleteAccountKeyPayload:
        """Delete this account key (but not others, if they exist).

        Args:
            provider: the AuthAlligator provider this account is for. (should
                be one of the ``ProviderType`` enum values)
            username: the AuthAlligator-provided username for the account (this
                will likely _not_ be the human-legible email/username)
            account_key: the AuthAlligator-specific secret key that proves we
                have access to the specific account

        Returns:
            DeleteAccountKeyPayload on success.

        Raises:
            AccountError in case of an account error.
        """
        query = """
            mutation deleteAccountKey($input: AccountAccessInput!) {
              deleteAccountKey(input: $input) {
                __typename
                ... on AccountError {
                  code
                  message
                  retryIn
                }
              }
            }
        """
        input_var = input_types.AccountAccessInput(
            provider=provider,
            username=username,
            account_key=account_key,
        )
        result = self._make_request(
            query=query,
            variables={"input": input_var.as_dict()},
            return_types=entities.Mutation,
        )

        delete_key = result.delete_account_key
        assert delete_key is not entities.OMITTED
        if isinstance(delete_key, entities.AccountError):
            raise exc.AccountError(
                code=delete_key.code,
                message=delete_key.message,
                retry_in=delete_key.retry_in,
            )
        return delete_key

    def delete_account(
        self,
        provider: enums.ProviderType,
        username: str,
    ) -> entities.DeleteAccountPayload:
        """Delete this account (and all associated account keys).

        Args:
            provider: the AuthAlligator provider this account is for. (should
                be one of the ``ProviderType`` enum values)
            username: the AuthAlligator-provided username for the account (this
                will likely _not_ be the human-legible email/username)

        Returns:
            DeleteAccountPayload on success.

        Raises:
            AccountError in case of an account error.
        """
        query = """
            mutation deleteAccount($input: DeleteAccountInput!) {
              deleteAccount(input: $input) {
                __typename
                ... on AccountError {
                  code
                  message
                  retryIn
                }
              }
            }
        """
        input_var = input_types.DeleteAccountInput(
            provider=provider,
            username=username,
        )
        result = self._make_request(
            query=query,
            variables={"input": input_var.as_dict()},
            return_types=entities.Mutation,
        )

        delete_account = result.delete_account
        assert delete_account is not entities.OMITTED
        if isinstance(delete_account, entities.AccountError):
            raise exc.AccountError(
                code=delete_account.code,
                message=delete_account.message,
                retry_in=delete_account.retry_in,
            )
        return delete_account
