"""
    .. module:: groupsupport
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains shared helpers used by the Tailscale
                   api-group classes.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict

from requests import Response

from automojo.restclient.tailscale.exceptions import classify_http_status


def raise_for_status(*, response: Response, action: str) -> None:
    """
        Reclassify a non-2xx HTTP response into a typed
        :class:`TailscaleApiError` subclass and raise it.

        :param response: The :class:`Response` to inspect.
        :param action: A short description of the attempted action.

        :returns: ``None``.

        :raises: :class:`TailscaleApiError` (or one of its subclasses
            :class:`TailscaleAuthError`, :class:`TailscaleNotFoundError`,
            :class:`TailscaleRateLimitError`, :class:`TailscaleServerError`)
            when the status is not 2xx.
    """
    status = response.status_code
    if 200 <= status < 300:
        return

    api_error = classify_http_status(status_code=status, action=action,
                                     response_body=response.text)
    raise api_error


def safe_json(*, response: Response) -> Dict[str, Any]:
    """
        Parse a response body as a JSON object, degrading to an empty dict.

        :param response: The :class:`Response` to parse.

        :returns: The decoded object, or an empty dict.
    """
    try:
        payload = response.json()
    except ValueError:
        rtnval: Dict[str, Any] = {}
        return rtnval

    if not isinstance(payload, dict):
        rtnval = {}
        return rtnval

    rtnval = payload
    return rtnval
