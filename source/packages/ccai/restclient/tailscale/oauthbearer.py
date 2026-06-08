"""
    .. module:: oauthbearer
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`OAuthBearer` cache object
                   and the :func:`mint_bearer` helper implementing the
                   Tailscale OAuth ``client_credentials`` flow.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os
import time

from typing import Callable, Optional

from requests import Response, Session

from ccai.errors.exceptions import HttpForbiddenError

from ccai.credentials.tailscaleoauthcredential import TailscaleOAuthCredential


OAUTH_TOKEN_LEAF = "/api/v2/oauth/token"


class OAuthBearer:
    """
        :class:`OAuthBearer` is the cached state for a minted OAuth bearer
        token. It stores the token text and the absolute monotonic-equivalent
        epoch time at which the token must be considered expired.

        The cache decision logic lives in :meth:`is_fresh`; the client uses
        it so the OAuth dance is invisible to callers.
    """

    def __init__(self, *, token: str, expires_at: float):
        """
            Initialize the cached bearer.

            :param token: The bearer token text.
            :param expires_at: Absolute epoch second at which the token
                expires.

            :returns: ``None``.
        """
        self._token = token
        self._expires_at = expires_at
        return

    @property
    def token(self) -> str:
        """
            The cached bearer token text.

            :returns: The bearer token string.
        """
        rtnval = self._token
        return rtnval

    @property
    def expires_at(self) -> float:
        """
            The absolute epoch second at which the token expires.

            :returns: The expiry epoch second.
        """
        rtnval = self._expires_at
        return rtnval

    def is_fresh(self, *, margin_seconds: float, now: float) -> bool:
        """
            Determine whether the cached token is still usable.

            :param margin_seconds: Number of seconds before expiry at which
                the token is treated as stale.
            :param now: The current epoch second.

            :returns: ``True`` when the token is fresh, ``False`` otherwise.
        """
        if self._token is None:
            rtnval = False
            return rtnval
        if len(self._token) == 0:
            rtnval = False
            return rtnval

        rtnval = (now + margin_seconds) < self._expires_at
        return rtnval


def mint_bearer(*, credential: TailscaleOAuthCredential, host_url: str,
                verify_certificate: bool,
                session_factory: Optional[Callable[[], Session]] = None,
                now: Optional[float] = None) -> OAuthBearer:
    """
        Mint a fresh OAuth bearer token using the ``client_credentials``
        flow against the Tailscale OAuth token endpoint.

        :param credential: The OAuth credential to authenticate with.
        :param host_url: The fully-qualified host URL (scheme + host).
        :param verify_certificate: Whether TLS certificates are verified.
        :param session_factory: Optional callable producing the
            :class:`Session` used for the mint call. Defaults to a fresh
            :class:`Session`.
        :param now: Optional epoch-second override for expiry computation.

        :returns: A populated :class:`OAuthBearer` cache object.

        :raises: :class:`HttpForbiddenError` when the OAuth endpoint rejects
            the credential or omits the ``access_token``.
    """
    if session_factory is None:
        mint_session = Session()
    else:
        mint_session = session_factory()

    mint_session.verify = verify_certificate

    token_url = "{}{}".format(host_url, OAUTH_TOKEN_LEAF)
    form_payload = {
        "client_id": credential.client_id,
        "client_secret": credential.client_secret,
        "grant_type": "client_credentials",
    }

    response: Response = mint_session.post(token_url, data=form_payload,
                                           verify=verify_certificate)

    if response.status_code < 200 or response.status_code >= 300:
        err_msg_lines = ["Failed to mint Tailscale OAuth token."]
        err_msg_lines.append("STATUS: {}".format(response.status_code))
        err_msg_lines.append("RESPONSE:")
        err_msg_lines.append(response.text)
        err_msg = os.linesep.join(err_msg_lines)
        raise HttpForbiddenError(err_msg)

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if payload is None or not isinstance(payload, dict):
        err_msg_lines = ["Tailscale OAuth token response was not JSON."]
        err_msg_lines.append("RESPONSE:")
        err_msg_lines.append(response.text)
        err_msg = os.linesep.join(err_msg_lines)
        raise HttpForbiddenError(err_msg)

    access_token = payload.get("access_token")
    if access_token is None or len(access_token) == 0:
        err_msg_lines = ["Tailscale OAuth token response missing 'access_token'."]
        err_msg_lines.append("RESPONSE:")
        err_msg_lines.append(response.text)
        err_msg = os.linesep.join(err_msg_lines)
        raise HttpForbiddenError(err_msg)

    expires_in = payload.get("expires_in")
    if expires_in is None:
        expires_in = 0

    if now is None:
        now_ts = time.time()
    else:
        now_ts = now

    expires_at = now_ts + float(expires_in)

    rtnval = OAuthBearer(token=access_token, expires_at=expires_at)
    return rtnval
