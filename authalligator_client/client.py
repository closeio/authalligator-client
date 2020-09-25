from typing import Any, Dict, Type, TypeVar, Union

import attr
import requests
import structlog

from . import entities, enums, exceptions as exc, input_types

logger = structlog.get_logger()

# helper for typing _make_request
T = TypeVar("T", bound=entities.BaseAAEntity)


@attr.attrs
class Client(object):
    token: str = attr.attrib()
    service_url: str = attr.attrib()

    timeout: int = attr.attrib(default=10)

    def _make_request(
        self,
        query: str,
        variables: Dict[str, Any],
        return_types: Type[T],
    ) -> T:
        response = requests.post(
            f"{self.service_url}/graphql",
            json={"query": query, "variables": variables},
            auth=(self.token, ""),
            timeout=self.timeout,
        )

        # responses (even for errors) should always be HTTP 200
        if response.status_code != 200:
            exc_cls: Type[exc.AuthAlligatorException]
            if response.status_code in (401, 403):
                exc_cls = exc.AuthAlligatorUnauthorizedError
            else:
                exc_cls = exc.UnexpectedStatusCode

            raise exc_cls(status_code=response.status_code, content=response.content)

        result = response.json()

        # errors are also unexpected
        errors = result.get("errors")
        if errors:
            raise exc.AuthAlligatorQueryError(errors=errors)

        data = result["data"]
        return entities.entity_converter(return_types)(data)

    def authorize_account(
        self,
        provider: enums.ProviderType,
        authorization_code: str,
        redirect_uri: str,
    ) -> Union[entities.AuthorizeAccountPayload, entities.AccountError]:
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
        return result.authorize_account

    def query_account(
        self, provider: enums.ProviderType, username: str, account_key: str
    ) -> Union[entities.Account, entities.AccountError]:
        """Obtain a valid access token.

        Args:
            provider: the AuthAlligator provider this account is for. (should
                be one of the ``ProviderType`` enum values)
            username: the AuthAlligator-provided username for the account (this
                will likely _not_ be the human-legible email/username)
            account_key: the AuthAlligator-specific secret key that proves we
                have access to the specific account

        Returns:
            The access token and expiration time for said access token.
        """
        query = """
            query getAccount($access: AccountAccessInput!) {
              account(access: $access) {
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
            variables={"access": input_var.as_dict()},
            return_types=entities.Query,
        )
        assert result.account is not entities.OMITTED
        return result.account
