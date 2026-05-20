"""
    .. module:: dnsgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`DnsGroup` api group
                   exposing the tailnet DNS endpoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List

from automojo.errors.exceptions import SemanticError

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.restclient.tailscale.aspectstailscale import (
    AspectsTailscale, DEFAULT_TAILSCALE_ASPECTS
)
from automojo.restclient.tailscale.apigroups.groupsupport import (
    raise_for_status, safe_json
)


class DnsGroup(RestApiGroup):
    """
        :class:`DnsGroup` exposes the tailnet DNS configuration endpoints —
        nameservers, preferences, and search paths. Each resource has a
        get / set pair.
    """

    BASE_LEAF = "/api/v2"

    def get_nameservers(self, *,
                        aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> List[str]:
        """
            Fetch the configured global DNS nameservers.

            :param aspects: Behaviour control for the call.

            :returns: A list of nameserver address strings.
        """
        payload = self._get_resource(resource="nameservers", action="get nameservers",
                                     aspects=aspects)
        dns_list = payload.get("dns")
        if dns_list is None:
            dns_list = []
        rtnval = list(dns_list)
        return rtnval

    def set_nameservers(self, *, nameservers: List[str],
                        aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            Replace the configured global DNS nameservers.

            :param nameservers: The complete replacement nameserver list.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``nameservers`` is ``None``.
        """
        if nameservers is None:
            raise SemanticError("'nameservers' must be a list of strings.")

        body: Dict[str, Any] = {"dns": list(nameservers)}
        self._set_resource(resource="nameservers", body=body,
                           action="set nameservers", aspects=aspects)
        return

    def get_preferences(self, *,
                        aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> Dict[str, Any]:
        """
            Fetch the tailnet DNS preferences.

            :param aspects: Behaviour control for the call.

            :returns: The DNS preferences dictionary.
        """
        rtnval = self._get_resource(resource="preferences",
                                    action="get dns preferences", aspects=aspects)
        return rtnval

    def set_preferences(self, *, preferences: Dict[str, Any],
                        aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            Replace the tailnet DNS preferences.

            :param preferences: The DNS preferences dictionary.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``preferences`` is ``None``.
        """
        if preferences is None:
            raise SemanticError("'preferences' must be a dictionary.")

        self._set_resource(resource="preferences", body=preferences,
                           action="set dns preferences", aspects=aspects)
        return

    def get_search_paths(self, *,
                         aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> List[str]:
        """
            Fetch the tailnet DNS search paths.

            :param aspects: Behaviour control for the call.

            :returns: A list of search-path strings.
        """
        payload = self._get_resource(resource="searchpaths",
                                     action="get dns search paths", aspects=aspects)
        paths = payload.get("searchPaths")
        if paths is None:
            paths = []
        rtnval = list(paths)
        return rtnval

    def set_search_paths(self, *, search_paths: List[str],
                         aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            Replace the tailnet DNS search paths.

            :param search_paths: The complete replacement search-path list.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``search_paths`` is ``None``.
        """
        if search_paths is None:
            raise SemanticError("'search_paths' must be a list of strings.")

        body: Dict[str, Any] = {"searchPaths": list(search_paths)}
        self._set_resource(resource="searchpaths", body=body,
                           action="set dns search paths", aspects=aspects)
        return

    def _get_resource(self, *, resource: str, action: str,
                      aspects: AspectsTailscale) -> Dict[str, Any]:
        """
            Issue a GET against a tailnet DNS sub-resource.

            :param resource: The DNS sub-resource leaf name.
            :param action: A short description for error reporting.
            :param aspects: Behaviour control for the call.

            :returns: The decoded JSON object.
        """
        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "dns", resource])
        response = client.request(method="GET", leaf=leaf, aspects=aspects)
        raise_for_status(response=response, action=action)

        rtnval = safe_json(response=response)
        return rtnval

    def _set_resource(self, *, resource: str, body: Dict[str, Any],
                      action: str, aspects: AspectsTailscale) -> None:
        """
            Issue a POST against a tailnet DNS sub-resource.

            :param resource: The DNS sub-resource leaf name.
            :param body: The request body to send.
            :param action: A short description for error reporting.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        client = self.client
        leaf = self.build_leaf(parts=["tailnet", client.tailnet, "dns", resource])
        response = client.request(method="POST", leaf=leaf, json_body=body,
                                  aspects=aspects)
        raise_for_status(response=response, action=action)
        return
