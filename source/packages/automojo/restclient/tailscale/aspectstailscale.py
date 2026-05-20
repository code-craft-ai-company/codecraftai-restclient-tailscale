"""
    .. module:: aspectstailscale
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`AspectsTailscale` class
                   used to control behaviour of Tailscale REST calls.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional, Tuple

import logging

from requests import Session

from automojo.restclient.base.aspectsrest import (
    ActionPattern, AspectsRest, LoggingPattern,
    DEFAULT_COMPLETION_TIMEOUT, DEFAULT_COMPLETION_INTERVAL,
    DEFAULT_CONNECTION_TIMEOUT, DEFAULT_INACTIVITY_TIMEOUT,
    DEFAULT_MONITOR_DELAY, DEFAULT_RETRY_LOGGING_INTERVAL,
    DEFAULT_LOGGING_PATTERN, DEFAULT_MUST_CONNECT,
    DEFAULT_ALLOWED_ERROR_CODES, DEFAULT_ALLOWED_CONNECTION_EXCEPTIONS
)


DEFAULT_TAILNET_TTL_SECONDS = 900
DEFAULT_OAUTH_REFRESH_MARGIN_SECONDS = 60


class AspectsTailscale(AspectsRest):
    """
        :class:`AspectsTailscale` extends :class:`AspectsRest` with Tailscale
        behaviour knobs — default auth-key TTL and OAuth refresh margin.

        The class keeps the standard REST aspects untouched; the additional
        fields are stored after the frozen-flag flip in the parent class.
        No behaviour-modifying decorators are used — all behaviour is
        carried by this aspects object.
    """

    def __init__(self, *, action_pattern: ActionPattern = ActionPattern.SINGLE_CALL,
                 completion_timeout: float = DEFAULT_COMPLETION_TIMEOUT,
                 completion_interval: float = DEFAULT_COMPLETION_INTERVAL,
                 connection_timeout: float = DEFAULT_CONNECTION_TIMEOUT,
                 inactivity_timeout: float = DEFAULT_INACTIVITY_TIMEOUT,
                 monitor_delay: float = DEFAULT_MONITOR_DELAY,
                 logging_pattern: LoggingPattern = DEFAULT_LOGGING_PATTERN,
                 retry_logging_interval: int = DEFAULT_RETRY_LOGGING_INTERVAL,
                 allowed_error_codes: Tuple[int, ...] = DEFAULT_ALLOWED_ERROR_CODES,
                 allowed_connection_exceptions: Tuple[BaseException, ...] = DEFAULT_ALLOWED_CONNECTION_EXCEPTIONS,
                 must_connect: bool = DEFAULT_MUST_CONNECT,
                 logger: Optional[logging.Logger] = None,
                 session: Optional[Session] = None,
                 tailnet_default_ttl_seconds: int = DEFAULT_TAILNET_TTL_SECONDS,
                 oauth_refresh_margin_seconds: int = DEFAULT_OAUTH_REFRESH_MARGIN_SECONDS):
        """
            Initialize a set of Tailscale REST call aspects.

            :param action_pattern: Default action pattern for calls.
            :param completion_timeout: Time in seconds to wait for completion.
            :param completion_interval: Polling interval when waiting.
            :param connection_timeout: Timeout for establishing connections.
            :param inactivity_timeout: Timeout for inactivity in seconds.
            :param monitor_delay: Delay before monitoring begins.
            :param logging_pattern: Pattern used for call logging.
            :param retry_logging_interval: Interval for retry log messages.
            :param allowed_error_codes: HTTP status codes considered success.
            :param allowed_connection_exceptions: Exceptions allowed during
                connect.
            :param must_connect: Whether a connection must be established.
            :param logger: Logger to use for messages.
            :param session: Requests session to reuse.
            :param tailnet_default_ttl_seconds: Default TTL for minted auth
                keys when callers omit an explicit TTL.
            :param oauth_refresh_margin_seconds: Number of seconds before
                expiry at which OAuth bearer tokens SHALL be refreshed.

            :returns: ``None``.
        """
        super().__init__(action_pattern=action_pattern,
                         completion_timeout=completion_timeout,
                         completion_interval=completion_interval,
                         connection_timeout=connection_timeout,
                         inactivity_timeout=inactivity_timeout,
                         monitor_delay=monitor_delay,
                         logging_pattern=logging_pattern,
                         retry_logging_interval=retry_logging_interval,
                         allowed_error_codes=allowed_error_codes,
                         allowed_connection_exceptions=allowed_connection_exceptions,
                         must_connect=must_connect,
                         logger=logger,
                         session=session)

        # The parent class freezes after __init__; flip the flag, assign the
        # extra attributes, and re-freeze so the aspects stay immutable.
        object.__setattr__(self, "__frozen__", False)
        self.tailnet_default_ttl_seconds = tailnet_default_ttl_seconds
        self.oauth_refresh_margin_seconds = oauth_refresh_margin_seconds
        object.__setattr__(self, "__frozen__", True)
        return


DEFAULT_TAILSCALE_ASPECTS = AspectsTailscale()
