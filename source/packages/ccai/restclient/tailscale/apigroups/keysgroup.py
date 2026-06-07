"""
    .. module:: keysgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`KeysGroup` api group
                   exposing the Tailscale auth-key / API-key endpoints.

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
from ccai.restclient.tailscale.model.tailscalekey import TailscaleKey


class KeysGroup(RestApiGroup):
    """
        :class:`KeysGroup` exposes the Tailscale key-management endpoints —
        list, get, mint, and delete. The mint operation builds the nested
        ``capabilities`` request body required by the upstream API.
    """

    BASE_LEAF = "/api/v2"

    def list(self, *,
             aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> List[TailscaleKey]:
        """
            List every key owned within the tailnet.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`TailscaleKey` models.
        """
        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "keys"])
        response = client.request(method="GET", leaf=leaf,
                                  params={"all": "true"}, aspects=aspects)
        raise_for_status(response=response, action="list keys")

        payload = response.json()
        raw_keys = payload.get("keys")
        if raw_keys is None:
            raw_keys = []

        rtnval: List[TailscaleKey] = []
        for entry in raw_keys:
            rtnval.append(TailscaleKey.from_dict(entry))

        return rtnval

    def iter(self, *,
             aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> Iterator[TailscaleKey]:
        """
            Iterate every key owned within the tailnet.

            :param aspects: Behaviour control for the call.

            :returns: An iterator over :class:`TailscaleKey` models.
        """
        keys = self.list(aspects=aspects)
        for key in keys:
            yield key
        return

    def get(self, *, key_id: str,
            aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> TailscaleKey:
        """
            Retrieve a single key by identifier.

            :param key_id: The key identifier.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`TailscaleKey` model.

            :raises: :class:`SemanticError` when ``key_id`` is empty.
        """
        self._require_key_id(key_id=key_id)

        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "keys", key_id])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        raise_for_status(response=response, action="get key")

        rtnval = TailscaleKey.from_dict(response.json())
        return rtnval

    def mint(self, *, reusable: bool, ephemeral: bool, tags: List[str],
             ttl_seconds: int,
             aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> TailscaleKey:
        """
            Mint a new auth key bound to ``tags``.

            :param reusable: Whether the key may be reused across multiple
                node bring-ups.
            :param ephemeral: Whether the resulting node registration is
                ephemeral.
            :param tags: Tags to bind to the key. An empty list omits the
                ``tags`` field.
            :param ttl_seconds: Requested TTL in seconds; must be > 0.
            :param aspects: Behaviour control for the call.

            :returns: A :class:`TailscaleKey` model carrying the minted key.

            :raises: :class:`SemanticError` when ``ttl_seconds`` is not
                positive.
        """
        if ttl_seconds is None:
            raise SemanticError("'ttl_seconds' must be a positive integer.")
        if ttl_seconds <= 0:
            raise SemanticError("'ttl_seconds' must be a positive integer.")

        body = self.build_authkey_body(reusable=reusable, ephemeral=ephemeral,
                                       tags=tags, ttl_seconds=ttl_seconds)

        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "keys"])
        response = client.request(method="POST", leaf=leaf,
                                  params={"all": "true"}, json_body=body,
                                  aspects=aspects)
        raise_for_status(response=response, action="mint key")

        rtnval = TailscaleKey.from_dict(response.json())
        return rtnval

    def delete(self, *, key_id: str,
               aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            Delete a key. A 404 is treated as already-removed.

            :param key_id: The key identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``key_id`` is empty or when
                the API returns a non-2xx, non-404 response.
        """
        self._require_key_id(key_id=key_id)

        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "keys", key_id])
        response = client.request(method="DELETE", leaf=leaf, aspects=aspects)

        status = response.status_code
        if 200 <= status < 300:
            return
        if status == 404:
            return

        raise_for_status(response=response, action="delete key")
        return

    def build_authkey_body(self, *, reusable: bool, ephemeral: bool,
                           tags: List[str],
                           ttl_seconds: int) -> Dict[str, Any]:
        """
            Build the JSON body for a key-mint request.

            :param reusable: Whether the minted key is reusable.
            :param ephemeral: Whether the minted key is ephemeral.
            :param tags: Tags to bind to the key. Empty list omits the field.
            :param ttl_seconds: Requested key TTL in seconds.

            :returns: A dictionary suitable for serialization as JSON.
        """
        create_block: Dict[str, Any] = {
            "reusable": reusable,
            "ephemeral": ephemeral,
            "preauthorized": True,
        }

        if tags is not None and len(tags) > 0:
            create_block["tags"] = list(tags)

        rtnval: Dict[str, Any] = {
            "capabilities": {
                "devices": {
                    "create": create_block,
                },
            },
            "expirySeconds": ttl_seconds,
        }
        return rtnval

    def _require_key_id(self, *, key_id: str) -> None:
        """
            Validate a key identifier argument.

            :param key_id: The key identifier to check.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``key_id`` is empty.
        """
        if key_id is None:
            raise SemanticError("'key_id' must be a non-empty string.")
        if len(key_id) == 0:
            raise SemanticError("'key_id' must be a non-empty string.")
        return
