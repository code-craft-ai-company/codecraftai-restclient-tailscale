"""
    .. module:: devicesgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`DevicesGroup` api group
                   exposing the Tailscale device endpoints.

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
from ccai.restclient.tailscale.apigroups.groupsupport import raise_for_status
from ccai.restclient.tailscale.model.tailscaledevice import TailscaleDevice


class DevicesGroup(RestApiGroup):
    """
        :class:`DevicesGroup` exposes the Tailscale device-management
        endpoints — list, get, delete, and the authorize / tag / key-expiry
        mutations. List responses are not cursor-paged by the upstream API,
        so :meth:`iter` walks the single-page result for interface
        uniformity.
    """

    BASE_LEAF = "/api/v2"

    def list(self, *,
             aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> List[TailscaleDevice]:
        """
            List every device registered in the tailnet.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`TailscaleDevice` models.
        """
        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "devices"])
        response = client.request(method="GET", leaf=leaf,
                                  params={"fields": "all"}, aspects=aspects)
        raise_for_status(response=response, action="list devices")

        payload = response.json()
        raw_devices = payload.get("devices")
        if raw_devices is None:
            raw_devices = []

        rtnval: List[TailscaleDevice] = []
        for entry in raw_devices:
            rtnval.append(TailscaleDevice.from_dict(entry))

        return rtnval

    def iter(self, *,
             aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> Iterator[TailscaleDevice]:
        """
            Iterate every device registered in the tailnet.

            :param aspects: Behaviour control for the call.

            :returns: An iterator over :class:`TailscaleDevice` models.
        """
        devices = self.list(aspects=aspects)
        for device in devices:
            yield device
        return

    def get(self, *, device_id: str,
            aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> TailscaleDevice:
        """
            Retrieve a single device by identifier.

            :param device_id: The provider-assigned device identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`TailscaleDevice` model.

            :raises: :class:`SemanticError` when ``device_id`` is empty.
        """
        self._require_device_id(device_id=device_id)

        client = self.client
        leaf = self.build_leaf(parts=["device", device_id])
        response = client.request(method="GET", leaf=leaf,
                                  params={"fields": "all"}, aspects=aspects)
        raise_for_status(response=response, action="get device")

        rtnval = TailscaleDevice.from_dict(response.json())
        return rtnval

    def delete(self, *, device_id: str,
               aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            De-register a device. A 404 is treated as already-removed.

            :param device_id: The provider-assigned device identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``device_id`` is empty or
                when the API returns a non-2xx, non-404 response.
        """
        self._require_device_id(device_id=device_id)

        client = self.client
        leaf = self.build_leaf(parts=["device", device_id])
        response = client.request(method="DELETE", leaf=leaf, aspects=aspects)

        status = response.status_code
        if 200 <= status < 300:
            return
        if status == 404:
            return

        raise_for_status(response=response, action="delete device")
        return

    def set_authorized(self, *, device_id: str, authorized: bool,
                       aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            Set the authorized flag on a device.

            :param device_id: The provider-assigned device identifier.
            :param authorized: The desired authorized state.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self._require_device_id(device_id=device_id)

        client = self.client
        leaf = self.build_leaf(parts=["device", device_id, "authorized"])
        body: Dict[str, Any] = {"authorized": authorized}
        response = client.request(method="POST", leaf=leaf, json_body=body,
                                  aspects=aspects)
        raise_for_status(response=response, action="set device authorized")
        return

    def set_tags(self, *, device_id: str, tags: List[str],
                 aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            Replace the tag set on a device.

            :param device_id: The provider-assigned device identifier.
            :param tags: The complete replacement tag list.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self._require_device_id(device_id=device_id)
        if tags is None:
            raise SemanticError("'tags' must be a list of tag strings.")

        client = self.client
        leaf = self.build_leaf(parts=["device", device_id, "tags"])
        body: Dict[str, Any] = {"tags": list(tags)}
        response = client.request(method="POST", leaf=leaf, json_body=body,
                                  aspects=aspects)
        raise_for_status(response=response, action="set device tags")
        return

    def set_key_expiry_disabled(self, *, device_id: str, disabled: bool,
                                aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            Enable or disable key-expiry for a device.

            :param device_id: The provider-assigned device identifier.
            :param disabled: When ``True``, key expiry is disabled.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self._require_device_id(device_id=device_id)

        client = self.client
        leaf = self.build_leaf(parts=["device", device_id, "key"])
        body: Dict[str, Any] = {"keyExpiryDisabled": disabled}
        response = client.request(method="POST", leaf=leaf, json_body=body,
                                  aspects=aspects)
        raise_for_status(response=response, action="set device key expiry")
        return

    def _require_device_id(self, *, device_id: str) -> None:
        """
            Validate a device identifier argument.

            :param device_id: The device identifier to check.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``device_id`` is empty.
        """
        if device_id is None:
            raise SemanticError("'device_id' must be a non-empty string.")
        if len(device_id) == 0:
            raise SemanticError("'device_id' must be a non-empty string.")
        return
