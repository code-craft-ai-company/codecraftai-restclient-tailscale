"""
    .. module:: aclsgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`AclsGroup` api group
                   exposing the tailnet ACL document endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, Optional, Tuple

from ccai.errors.exceptions import SemanticError

from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.tailscale.aspectstailscale import (
    AspectsTailscale, DEFAULT_TAILSCALE_ASPECTS
)
from ccai.restclient.tailscale.apigroups.groupsupport import raise_for_status


class AclsGroup(RestApiGroup):
    """
        :class:`AclsGroup` exposes the tailnet ACL document endpoints —
        :meth:`get` to fetch the document and its ETag, and :meth:`put` to
        replace it with optional optimistic concurrency via an ``If-Match``
        header.
    """

    BASE_LEAF = "/api/v2"

    def get(self, *,
            aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> Tuple[Dict[str, Any], Optional[str]]:
        """
            Fetch the current ACL document and its ETag.

            :param aspects: Behaviour control for the call.

            :returns: A tuple of ``(acl_document, etag)`` where ``etag`` may
                be ``None`` when the API omits the header.
        """
        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "acl"])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        raise_for_status(response=response, action="get acl")

        acl_document = response.json()
        etag = response.headers.get("ETag")

        rtnval = (acl_document, etag)
        return rtnval

    def put(self, *, acl_doc: Dict[str, Any], etag: Optional[str] = None,
            aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> Dict[str, Any]:
        """
            Replace the tailnet ACL document.

            When ``etag`` is supplied, an ``If-Match`` header is attached so
            the update is rejected by the server when the document has
            changed since it was read.

            :param acl_doc: The ACL document to apply.
            :param etag: Optional ETag for optimistic concurrency.
            :param aspects: Behaviour control for the call.

            :returns: The applied ACL document echoed by the API.

            :raises: :class:`SemanticError` when ``acl_doc`` is ``None``.
        """
        if acl_doc is None:
            raise SemanticError("'acl_doc' must be a dictionary.")

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if etag is not None:
            headers["If-Match"] = etag

        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "acl"])
        response = client.request(method="POST", leaf=leaf, json_body=acl_doc,
                                  headers=headers, aspects=aspects)
        raise_for_status(response=response, action="put acl")

        try:
            rtnval = response.json()
        except ValueError:
            rtnval = {}

        return rtnval
