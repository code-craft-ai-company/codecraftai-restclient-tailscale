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


import os

from typing import Any, Dict

from requests import Response

from automojo.errors.exceptions import SemanticError


def raise_for_status(*, response: Response, action: str) -> None:
    """
        Raise a descriptive :class:`SemanticError` for a non-2xx response.

        :param response: The :class:`Response` to inspect.
        :param action: A short description of the attempted action.

        :returns: ``None``.

        :raises: :class:`SemanticError` when the status is not 2xx.
    """
    status = response.status_code
    if 200 <= status < 300:
        return

    err_msg_lines = ["Tailscale API call failed: {}.".format(action)]
    err_msg_lines.append("STATUS: {}".format(status))
    err_msg_lines.append("RESPONSE:")
    err_msg_lines.append(response.text)
    err_msg = os.linesep.join(err_msg_lines)
    raise SemanticError(err_msg)


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
