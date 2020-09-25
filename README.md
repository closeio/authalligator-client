# AuthAlligator Client
A python client for the AuthAlligator OAuth token management service.

## Usage

```python
from authalligator_client.client import Client
from authalligator_client.enums import ProviderType
from authalligator_client.entities import AccountError

client = Client(token='my-secret-token', service_url='authalligator.example.com')

authorize_result = client.authorize_account(
    provider=ProviderType.MICROSOFT,
    authorization_code='my-code',
    redirect_uri='mysite.example.com/oauth2/microsoft/callback',
)
if isinstance(authorize_result, AccountError):
    print("encountered an error!", authorize_result.code, authorize_result.message)
else:
    print("Got an access token + key for refreshing!")
    print("Access Key:", authorize_result.access_key)
    print("Username:", authorize_result.account.username)
    print("Provider:", authorize_result.account.provider)
    print("Access Token:", authorize_result.account.access_token)
    print("Access Token Expiry:", authorize_result.account.access_token_expires_at)

account_result = client.query_account(
    provider=authorize_result.account.provider,
    username=authorize_result.account.username,
    account_key=authorize_result.account_key,
)
if isinstance(account_result, AccountError):
    print("Encountered an error!", account_result.code, account_result.message)
else:
    print("New Access Token:". account_result.access_token)

```

## Running Tests

Running tests is simple with docker:

```bash
$ docker-compose run --rm authalligator_client pytest
```
