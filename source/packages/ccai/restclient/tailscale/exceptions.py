"""
    .. module:: exceptions
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the typed exception hierarchy raised
                   by the Tailscale REST client when the upstream API returns
                   a non-2xx HTTP response.

    The ``codecraftai-restclient-tailscale`` package is a standalone vendor REST
    client. The HTTP-status-specific failure types live here so callers can
    react to authentication, not-found, rate-limit and server failures
    without parsing message text.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os

from typing import Optional


class TailscaleApiError(Exception):
    """
        Base class for every error raised when the Tailscale API returns a
        non-2xx HTTP response. The originating status code and response body
        are preserved so callers may inspect them directly.
    """

    def __init__(self, message: str, *, status_code: Optional[int] = None,
                 response_body: Optional[str] = None):
        """
            Initialize the API error with HTTP response context.

            :param message: A descriptive, multi-line error message.
            :param status_code: The HTTP status code returned by the API.
            :param response_body: The raw response body text from the API.

            :returns: ``None``.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        return


class TailscaleAuthError(TailscaleApiError):
    """
        Raised when the Tailscale API rejects a request with a ``401`` or
        ``403`` status — the credential is missing, invalid, or lacks the
        scope required for the attempted action.
    """


class TailscaleNotFoundError(TailscaleApiError):
    """
        Raised when the Tailscale API returns a ``404`` status — the
        addressed tailnet, device, key or other resource does not exist.
    """


class TailscaleRateLimitError(TailscaleApiError):
    """
        Raised when the Tailscale API returns a ``429`` status — the caller
        has exceeded the upstream request-rate budget.
    """


class TailscaleServerError(TailscaleApiError):
    """
        Raised when the Tailscale API returns a ``5xx`` status — the upstream
        service failed to process an otherwise well-formed request.
    """


def classify_http_status(*, status_code: int, action: str,
                          response_body: str) -> TailscaleApiError:
    """
        Map a non-2xx HTTP status code onto the most specific
        :class:`TailscaleApiError` subclass and build it with descriptive,
        multi-line context.

        :param status_code: The HTTP status code returned by the API.
        :param action: A short description of the attempted action.
        :param response_body: The raw response body text from the API.

        :returns: A :class:`TailscaleApiError` (or subclass) instance ready
            to be raised by the caller.
    """
    if status_code in (401, 403):
        error_type = TailscaleAuthError
    elif status_code == 404:
        error_type = TailscaleNotFoundError
    elif status_code == 429:
        error_type = TailscaleRateLimitError
    elif 500 <= status_code < 600:
        error_type = TailscaleServerError
    else:
        error_type = TailscaleApiError

    err_msg_lines = ["Tailscale API call failed: {}.".format(action)]
    err_msg_lines.append("STATUS: {}".format(status_code))
    err_msg_lines.append("RESPONSE:")
    err_msg_lines.append(response_body)
    err_msg = os.linesep.join(err_msg_lines)

    rtnval = error_type(err_msg, status_code=status_code,
                        response_body=response_body)
    return rtnval


__all__ = [
    "TailscaleApiError",
    "TailscaleAuthError",
    "TailscaleNotFoundError",
    "TailscaleRateLimitError",
    "TailscaleServerError",
    "classify_http_status",
]
