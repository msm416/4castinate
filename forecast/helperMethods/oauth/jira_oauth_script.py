import base64
from urllib.parse import parse_qsl

from tlslite.utils import keyfactory
import oauth2 as oauth
from pathlib import Path


def create_oauth_client(consumer, sign_method, token=None):
    client = oauth.Client(consumer, token)
    client.set_signature_method(sign_method)
    client.disable_ssl_certificate_validation = True  # TODO: IS THIS THE RIGHT THING?
    return client


class SignatureMethod_RSA_SHA1(oauth.SignatureMethod):
    name = 'RSA-SHA1'

    def signing_base(self, request, consumer, token):
        if not hasattr(request, 'normalized_url') or request.normalized_url is None:
            raise ValueError("Base URL for request is not set.")

        sig = (oauth.escape(request.method),
               oauth.escape(request.normalized_url),
               oauth.escape(request.get_normalized_parameters()),)

        key = '%s&' % oauth.escape(consumer.secret)
        if token:
            key += oauth.escape(token.secret)
        raw = '&'.join(sig)
        return key, raw

    def sign(self, request, consumer, token):
        """Builds the base signature string."""
        key, raw = self.signing_base(request, consumer, token)

        with open((Path(__file__).parent / 'jira_privatekey.pem').resolve(), 'r') as f:
            data = f.read()

        private_key_string = data.strip()

        private_key = keyfactory.parsePrivateKey(private_key_string)
        signature = private_key.hashAndSign(bytes(raw, encoding='utf8'))

        return base64.b64encode(signature)


def get_access_token():
    consumer_key = 'OauthKey'
    consumer_secret = 'dont_care'

    request_token_url = 'https://4cast.atlassian.net/plugins/servlet/oauth/request-token'
    access_token_url = 'https://4cast.atlassian.net/plugins/servlet/oauth/access-token'
    authorize_url = 'https://4cast.atlassian.net/plugins/servlet/oauth/authorize'

    data_url = 'https://4cast.atlassian.net/rest/agile/1.0/issue/OB-26'

    consumer = oauth.Consumer(consumer_key, consumer_secret)

    client = create_oauth_client(consumer, SignatureMethod_RSA_SHA1())

    # Lets try to access a JIRA issue (BULK-1). We should get a 401.
    resp, content = client.request(data_url, "GET")
    if resp['status'] != '401':
        raise Exception("Should have no access!")

    # Step 1: Get a request token. This is a temporary token that is used for
    # having the user authorize an access token and to sign the request to obtain
    # said access token.
    resp, content = client.request(request_token_url, "POST")
    if resp['status'] != '200':
        raise Exception(f"Invalid response {resp['status']}: {content}")

    request_token = dict(parse_qsl(content))

    request_token = dict(map(lambda item:
                             (item[0].decode('utf-8'), item[1].decode('utf-8')),
                             request_token.items()))

    print("Request Token:")
    print("    - oauth_token        = %s" % request_token['oauth_token'])
    print("    - oauth_token_secret = %s" % request_token['oauth_token_secret'])

    # Step 2: Redirect to the provider. Since this is a CLI script we do not
    # redirect. In a web application you would redirect the user to the URL
    # below.
    print("Go to the following link in your browser:")
    print("%s?oauth_token=%s" % (authorize_url, request_token['oauth_token']))

    # After the user has granted access to you, the consumer, the provider will
    # redirect you to whatever URL you have told them to redirect to. You can
    # usually define this in the oauth_callback argument as well.
    accepted = 'n'
    while accepted.lower() == 'n':
        accepted = input('Have you authorized me? (y/n) ')

    # Step 3: Once the consumer has redirected the user back to the oauth_callback
    # URL you can request the access token the user has approved. You use the
    # request token to sign this request. After this is done you throw away the
    # request token and use the access token returned. You should store this
    # access token somewhere safe, like a database, for future use.
    token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])

    client = create_oauth_client(consumer, SignatureMethod_RSA_SHA1(), token)

    resp, content = client.request(access_token_url, "POST")

    access_token_parts = dict(parse_qsl(content))
    access_token_parts = dict(
        map(lambda item: (item[0].decode('utf-8'), item[1].decode('utf-8')), access_token_parts.items()))

    print("Access Token:")
    print("    - oauth_token        = %s" % access_token_parts['oauth_token'])
    print("    - oauth_token_secret = %s" % access_token_parts['oauth_token_secret'])
    print("You may now access protected resources using the access tokens above.")

    # Now lets try to access the same issue again with the access token. We should get a 200!
    access_token = oauth.Token(access_token_parts['oauth_token'], access_token_parts['oauth_token_secret'])

    client = create_oauth_client(consumer, SignatureMethod_RSA_SHA1(), access_token)

    resp, content = client.request(data_url, "GET")
    if resp['status'] != '200':
        raise Exception("Should have access!")


if __name__ == '__main__':
    get_access_token()
