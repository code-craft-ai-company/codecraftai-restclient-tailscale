"""
    .. module:: testsupport
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Shared construction helpers for the Tailscale REST client
                   test suite.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.credentials.tailscaleauthkeycredential import TailscaleAuthKeyCredential
from ccai.credentials.tailscaleoauthcredential import TailscaleOAuthCredential

from ccai.restclient.tailscale.tailscaleclient import TailscaleClient


TEST_HOST = "api.tailscale.test"
TEST_TAILNET = "example.com"


def make_authkey_credential() -> TailscaleAuthKeyCredential:
    """
        Build a :class:`TailscaleAuthKeyCredential` for tests.

        :returns: A populated auth-key credential.
    """
    rtnval = TailscaleAuthKeyCredential(identifier="ts-test-key",
                                        categories=["tailscale-authkey"],
                                        authkey="tskey-auth-static-0001")
    return rtnval


def make_oauth_credential() -> TailscaleOAuthCredential:
    """
        Build a :class:`TailscaleOAuthCredential` for tests.

        :returns: A populated OAuth credential.
    """
    rtnval = TailscaleOAuthCredential(identifier="ts-test-oauth",
                                      categories=["tailscale-oauth"],
                                      client_id="ksTEST",
                                      client_secret="tskey-client-secret-TEST")
    return rtnval


def make_authkey_client() -> TailscaleClient:
    """
        Build a :class:`TailscaleClient` using a static auth-key credential.

        :returns: A constructed client.
    """
    rtnval = TailscaleClient(credential=make_authkey_credential(),
                             tailnet=TEST_TAILNET, host=TEST_HOST)
    return rtnval


def make_oauth_client() -> TailscaleClient:
    """
        Build a :class:`TailscaleClient` using an OAuth credential.

        :returns: A constructed client.
    """
    rtnval = TailscaleClient(credential=make_oauth_credential(),
                             tailnet=TEST_TAILNET, host=TEST_HOST)
    return rtnval
