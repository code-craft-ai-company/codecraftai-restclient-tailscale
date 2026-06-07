"""
    .. module:: posturegroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`PostureGroup` api group
                   exposing the Tailscale device-posture endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, Iterator, List

from ccai.errors.exceptions import SemanticError

from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.tailscale.aspectstailscale import (
    AspectsTailscale, DEFAULT_TAILSCALE_ASPECTS
)
from ccai.restclient.tailscale.apigroups.groupsupport import (
    raise_for_status, safe_json
)
from ccai.restclient.tailscale.model.tailscalepostureintegration import (
    TailscalePostureIntegration
)


class PostureGroup(RestApiGroup):
    """
        :class:`PostureGroup` exposes the Tailscale device-posture endpoints
        — posture integrations and the set of signing nodes.
    """

    BASE_LEAF = "/api/v2"

    def list_integrations(self, *,
                          aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> List[TailscalePostureIntegration]:
        """
            List the configured posture integrations.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`TailscalePostureIntegration` models.
        """
        client = self.client
        leaf = self.build_leaf(
            parts=["tailnet", client.tailnet, "posture", "integrations"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        raise_for_status(response=response, action="list posture integrations")

        payload = safe_json(response=response)
        raw_items = payload.get("integrations")
        if raw_items is None:
            raw_items = []

        rtnval: List[TailscalePostureIntegration] = []
        for entry in raw_items:
            rtnval.append(TailscalePostureIntegration.from_dict(entry))

        return rtnval

    def iter_integrations(self, *,
                          aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> Iterator[TailscalePostureIntegration]:
        """
            Iterate the configured posture integrations.

            :param aspects: Behaviour control for the call.

            :returns: An iterator over
                :class:`TailscalePostureIntegration` models.
        """
        integrations = self.list_integrations(aspects=aspects)
        for integration in integrations:
            yield integration
        return

    def get_integration(self, *, integration_id: str,
                         aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> TailscalePostureIntegration:
        """
            Retrieve a single posture integration by identifier.

            :param integration_id: The posture integration identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`TailscalePostureIntegration` model.

            :raises: :class:`SemanticError` when ``integration_id`` is empty.
        """
        if integration_id is None or len(integration_id) == 0:
            raise SemanticError("'integration_id' must be a non-empty string.")

        client = self.client
        leaf = self.build_leaf(parts=["posture", "integrations", integration_id])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        raise_for_status(response=response, action="get posture integration")

        rtnval = TailscalePostureIntegration.from_dict(response.json())
        return rtnval

    def list_signing_nodes(self, *,
                           aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> List[Dict[str, Any]]:
        """
            List the device-posture signing nodes for the tailnet.

            :param aspects: Behaviour control for the call.

            :returns: A list of signing-node dictionaries.
        """
        client = self.client
        leaf = self.build_leaf(
            parts=["tailnet", client.tailnet, "devices", "posture",
                   "integrations", "signing-nodes"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        raise_for_status(response=response, action="list signing nodes")

        payload = safe_json(response=response)
        nodes = payload.get("signingNodes")
        if nodes is None:
            nodes = []
        rtnval = list(nodes)
        return rtnval
