"""
    .. module:: tailscale
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Typed, aspect-driven REST client package for the Tailscale
                   public API (``api.tailscale.com/api/v2/``).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.tailscale.tailscaleclient import TailscaleClient
from ccai.restclient.tailscale.aspectstailscale import (
    AspectsTailscale, DEFAULT_TAILSCALE_ASPECTS
)


__all__ = ["TailscaleClient", "AspectsTailscale", "DEFAULT_TAILSCALE_ASPECTS"]
