"""
    .. module:: tailnetsgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TailnetsGroup` api group
                   exposing the tailnet settings endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict

from ccai.errors.exceptions import SemanticError

from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.tailscale.aspectstailscale import (
    AspectsTailscale, DEFAULT_TAILSCALE_ASPECTS
)
from ccai.restclient.tailscale.apigroups.groupsupport import raise_for_status
from ccai.restclient.tailscale.model.tailscaletailnetsettings import (
    TailscaleTailnetSettings
)


class TailnetsGroup(RestApiGroup):
    """
        :class:`TailnetsGroup` exposes the tailnet settings endpoints —
        :meth:`get_settings` and :meth:`update_settings`.
    """

    BASE_LEAF = "/api/v2"

    def get_settings(self, *,
                     aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> TailscaleTailnetSettings:
        """
            Fetch the tailnet settings.

            :param aspects: Behaviour control for the call.

            :returns: A :class:`TailscaleTailnetSettings` model.
        """
        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "settings"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        raise_for_status(response=response, action="get tailnet settings")

        rtnval = TailscaleTailnetSettings.from_dict(response.json())
        return rtnval

    def update_settings(self, *, settings: Dict[str, Any],
                        aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            Update the tailnet settings.

            :param settings: A dictionary of settings to patch.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``settings`` is ``None``.
        """
        if settings is None:
            raise SemanticError("'settings' must be a dictionary.")

        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "settings"])
        response = client.request(method="PATCH", leaf=leaf, json_body=settings,
                                  aspects=aspects)
        raise_for_status(response=response, action="update tailnet settings")
        return
