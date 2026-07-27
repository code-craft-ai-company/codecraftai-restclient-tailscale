"""
    .. module:: test_oauth
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for the OAuth bearer-token lifecycle — lazy mint,
                   cache hit, 401 re-mint-and-retry, and double-401 raise.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai import testbase


import requests_mock as rm_module

from ccai.errors.exceptions import HttpForbiddenError

from ccai.restclient.tailscale.exceptions import TailscaleAuthError

from ccai.restclient.tailscale.oauthbearer import OAuthBearer

from ccai.tests.restclient.tailscale.testsupport import (
    TEST_HOST, TEST_TAILNET, make_oauth_client
)


BASE = "https://{}".format(TEST_HOST)
TNET = "/api/v2/tailnet/{}".format(TEST_TAILNET)
TOKEN_URL = "{}/api/v2/oauth/token".format(BASE)
DEVICES_URL = "{}{}/devices".format(BASE, TNET)


def test_oauth_bearer_freshness():
    """
        :meth:`OAuthBearer.is_fresh` respects the refresh margin.
    """
    bearer = OAuthBearer(token="tok", expires_at=1000.0)
    assert bearer.is_fresh(margin_seconds=60, now=900.0) is True
    assert bearer.is_fresh(margin_seconds=60, now=950.0) is False
    assert bearer.is_fresh(margin_seconds=60, now=1100.0) is False
    return


def test_oauth_empty_token_never_fresh():
    """
        An :class:`OAuthBearer` with an empty token is never fresh.
    """
    bearer = OAuthBearer(token="", expires_at=99999999999.0)
    assert bearer.is_fresh(margin_seconds=0, now=0.0) is False
    return


def test_oauth_lazy_mint_on_first_call():
    """
        The OAuth bearer is minted lazily on the first API call.
    """
    client = make_oauth_client()
    with rm_module.Mocker() as mock:
        mock.post(TOKEN_URL, json={"access_token": "minted-1",
                                   "expires_in": 3600})
        mock.get(DEVICES_URL, json={"devices": []})

        assert client._bearer is None
        client.devices.list()

        history = [req.url for req in mock.request_history]
        assert history[0] == TOKEN_URL
        assert client._bearer.token == "minted-1"
    return


def test_oauth_cache_hit_no_remint():
    """
        A fresh cached bearer is reused — the token endpoint is hit once
        across multiple calls.
    """
    client = make_oauth_client()
    with rm_module.Mocker() as mock:
        mock.post(TOKEN_URL, json={"access_token": "minted-1",
                                   "expires_in": 3600})
        mock.get(DEVICES_URL, json={"devices": []})

        client.devices.list()
        client.devices.list()
        client.devices.list()

        token_calls = [req for req in mock.request_history
                       if req.url == TOKEN_URL]
        assert len(token_calls) == 1
    return


def test_oauth_401_triggers_single_remint_and_retry():
    """
        A 401 response triggers exactly one re-mint and one retry; the
        retry succeeds.
    """
    client = make_oauth_client()
    with rm_module.Mocker() as mock:
        mock.post(TOKEN_URL, [
            {"json": {"access_token": "stale", "expires_in": 3600}},
            {"json": {"access_token": "fresh", "expires_in": 3600}},
        ])
        mock.get(DEVICES_URL, [
            {"status_code": 401, "text": "unauthorized"},
            {"json": {"devices": []}, "status_code": 200},
        ])

        client.devices.list()

        token_calls = [req for req in mock.request_history
                       if req.url == TOKEN_URL]
        device_calls = [req for req in mock.request_history
                        if req.url.startswith(DEVICES_URL)]
        assert len(token_calls) == 2
        assert len(device_calls) == 2
        assert client._bearer.token == "fresh"
    return


def test_oauth_double_401_raises_forbidden():
    """
        A second 401 after re-mint raises a typed :class:`TailscaleAuthError`
        without looping.
    """
    client = make_oauth_client()
    with rm_module.Mocker() as mock:
        mock.post(TOKEN_URL, json={"access_token": "tok", "expires_in": 3600})
        mock.get(DEVICES_URL, status_code=401, text="still unauthorized")

        with testbase.raises(TailscaleAuthError) as excinfo:
            client.devices.list()
        assert excinfo.value.status_code == 401
        assert "still unauthorized" in excinfo.value.response_body

        device_calls = [req for req in mock.request_history
                        if req.url.startswith(DEVICES_URL)]
        assert len(device_calls) == 2
    return


def test_oauth_mint_failure_raises_forbidden():
    """
        A non-2xx OAuth token response raises :class:`HttpForbiddenError`.
    """
    client = make_oauth_client()
    with rm_module.Mocker() as mock:
        mock.post(TOKEN_URL, status_code=403, text="bad client")
        with testbase.raises(HttpForbiddenError):
            client.devices.list()
    return
