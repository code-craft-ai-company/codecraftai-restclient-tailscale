"""
    .. module:: tailscale
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Typed, aspect-driven REST client package for the Tailscale
                   public API (``api.tailscale.com/api/v2/``).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.tailscale.tailscaleclient import TailscaleClient
from automojo.restclient.tailscale.aspectstailscale import (
    AspectsTailscale, DEFAULT_TAILSCALE_ASPECTS
)


__all__ = ["TailscaleClient", "AspectsTailscale", "DEFAULT_TAILSCALE_ASPECTS"]
