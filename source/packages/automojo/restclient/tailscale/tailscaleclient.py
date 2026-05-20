"""
    .. module:: tailscaleclient
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TailscaleClient` REST
                   client for the Tailscale public API
                   (``api.tailscale.com/api/v2/``).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import ipaddress
import json
import os
import time

from typing import Any, Dict, List, Optional, Union

from requests import Response, Session

from automojo.errors.exceptions import (
    ConfigurationError, SemanticError
)

from automojo.restclient.tailscale.exceptions import TailscaleAuthError

from automojo.credentials.basecredential import BaseCredential
from automojo.credentials.tailscaleauthkeycredential import TailscaleAuthKeyCredential
from automojo.credentials.tailscaleoauthcredential import TailscaleOAuthCredential

from automojo.interfaces.ivpncontrolplane import VPNDeviceRecord

from automojo.restclient.base.restclientbase import RestClientBase

from automojo.restclient.tailscale.aspectstailscale import (
    AspectsTailscale, DEFAULT_TAILSCALE_ASPECTS
)
from automojo.restclient.tailscale.oauthbearer import OAuthBearer, mint_bearer

from automojo.restclient.tailscale.apigroups.devicesgroup import DevicesGroup
from automojo.restclient.tailscale.apigroups.keysgroup import KeysGroup
from automojo.restclient.tailscale.apigroups.aclsgroup import AclsGroup
from automojo.restclient.tailscale.apigroups.tailnetsgroup import TailnetsGroup
from automojo.restclient.tailscale.apigroups.dnsgroup import DnsGroup
from automojo.restclient.tailscale.apigroups.posturegroup import PostureGroup

from automojo.restclient.tailscale.model.tailscaledevice import TailscaleDevice


TAILSCALE_API_HOST = "api.tailscale.com"

CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")


class TailscaleClient(RestClientBase):
    """
        :class:`TailscaleClient` is the typed, aspect-driven REST client for
        the Tailscale public API. It is built on :class:`RestClientBase` and
        implements the
        :class:`automojo.interfaces.ivpncontrolplane.IVPNControlPlane`
        protocol so any consumer expecting a VPN control plane can substitute
        it transparently.

        The client exposes its surface through six api groups
        (:attr:`devices`, :attr:`keys`, :attr:`acls`, :attr:`tailnets`,
        :attr:`dns`, :attr:`posture`) and additionally provides the
        provider-neutral ``IVPNControlPlane`` methods which delegate to the
        groups and adapt typed models to the protocol dataclasses.

        Authentication is sourced from the supplied credential — either a
        :class:`TailscaleAuthKeyCredential` (static bearer) or a
        :class:`TailscaleOAuthCredential` (lazily minted, cached, refreshed
        OAuth bearer). All HTTP behaviour is carried by
        :class:`AspectsTailscale`; no behaviour-modifying decorators are
        used.
    """

    def __init__(self, *, credential: BaseCredential, tailnet: str = "-",
                 host: str = TAILSCALE_API_HOST,
                 aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS):
        """
            Initialize the Tailscale REST client.

            :param credential: Either a :class:`TailscaleAuthKeyCredential`
                or a :class:`TailscaleOAuthCredential`.
            :param tailnet: The tailnet identifier (commonly ``"-"`` for the
                default tailnet owned by the credential).
            :param host: Override host name for the REST endpoint.
            :param aspects: Default :class:`AspectsTailscale` applied when a
                call omits an explicit aspects argument.

            :returns: ``None``.

            :raises: :class:`ConfigurationError` when ``credential`` is not a
                Tailscale credential type.
        """
        if not isinstance(credential, (TailscaleAuthKeyCredential,
                                       TailscaleOAuthCredential)):
            err_msg_lines = ["TailscaleClient requires a Tailscale credential."]
            err_msg_lines.append("EXPECTED: TailscaleAuthKeyCredential or "
                                 "TailscaleOAuthCredential")
            err_msg_lines.append("FOUND: {}".format(type(credential).__name__))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        super().__init__(host=host, credential=credential, aspects=aspects)

        self._tailnet = tailnet
        self._bearer: Optional[OAuthBearer] = None
        self._static_bearer: Optional[str] = None

        if isinstance(credential, TailscaleAuthKeyCredential):
            self._static_bearer = credential.authkey

        self._devices = DevicesGroup(self)
        self._keys = KeysGroup(self)
        self._acls = AclsGroup(self)
        self._tailnets = TailnetsGroup(self)
        self._dns = DnsGroup(self)
        self._posture = PostureGroup(self)
        return

    @property
    def tailnet(self) -> str:
        """
            The tailnet identifier this client targets.

            :returns: The tailnet identifier string.
        """
        rtnval = self._tailnet
        return rtnval

    @property
    def devices(self) -> DevicesGroup:
        """
            The devices api group.

            :returns: The :class:`DevicesGroup` instance.
        """
        rtnval = self._devices
        return rtnval

    @property
    def keys(self) -> KeysGroup:
        """
            The keys api group.

            :returns: The :class:`KeysGroup` instance.
        """
        rtnval = self._keys
        return rtnval

    @property
    def acls(self) -> AclsGroup:
        """
            The acls api group.

            :returns: The :class:`AclsGroup` instance.
        """
        rtnval = self._acls
        return rtnval

    @property
    def tailnets(self) -> TailnetsGroup:
        """
            The tailnets api group.

            :returns: The :class:`TailnetsGroup` instance.
        """
        rtnval = self._tailnets
        return rtnval

    @property
    def dns(self) -> DnsGroup:
        """
            The dns api group.

            :returns: The :class:`DnsGroup` instance.
        """
        rtnval = self._dns
        return rtnval

    @property
    def posture(self) -> PostureGroup:
        """
            The posture api group.

            :returns: The :class:`PostureGroup` instance.
        """
        rtnval = self._posture
        return rtnval

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def request(self, *, method: str, leaf: str,
                params: Optional[Dict[str, str]] = None,
                json_body: Optional[Union[Dict[str, Any], list]] = None,
                headers: Optional[Dict[str, str]] = None,
                aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> Response:
        """
            Issue a single REST call against the Tailscale API.

            The call attaches the resolved bearer token, serializes
            ``json_body`` as raw JSON, and implements the
            mint-once-then-retry behaviour on a 401 response. A second 401
            raises :class:`TailscaleAuthError` without looping.

            :param method: HTTP method to invoke.
            :param leaf: API leaf path beginning with ``/``.
            :param params: Optional query-string parameters.
            :param json_body: Optional dict/list serialized as the body.
            :param headers: Optional additional request headers.
            :param aspects: Behaviour-control aspects for the call.

            :returns: The :class:`Response` object from the call.

            :raises: :class:`TailscaleAuthError` when a 401 persists after a
                single re-mint and retry.
        """
        attempt = 0
        response: Optional[Response] = None

        while True:
            session = self._authenticated_session(aspects=aspects,
                                                   force_remint=(attempt > 0))
            response = self._send(method=method, leaf=leaf, params=params,
                                  json_body=json_body, headers=headers,
                                  session=session, aspects=aspects)

            if response.status_code != 401:
                break

            if attempt >= 1:
                err_msg_lines = ["Tailscale API rejected the request after "
                                 "a bearer re-mint."]
                err_msg_lines.append("METHOD: {}".format(method))
                err_msg_lines.append("LEAF: {}".format(leaf))
                err_msg_lines.append("STATUS: {}".format(response.status_code))
                err_msg_lines.append("RESPONSE:")
                err_msg_lines.append(response.text)
                err_msg = os.linesep.join(err_msg_lines)
                raise TailscaleAuthError(err_msg,
                                         status_code=response.status_code,
                                         response_body=response.text)

            attempt = attempt + 1

        rtnval = response
        return rtnval

    def _authenticated_session(self, *, aspects: AspectsTailscale,
                               force_remint: bool) -> Session:
        """
            Build a :class:`Session` carrying a current bearer token.

            For OAuth credentials the bearer is minted lazily and cached;
            it is re-minted when stale or when ``force_remint`` is set.

            :param aspects: Behaviour-control aspects.
            :param force_remint: When ``True``, discard any cached bearer
                and mint a fresh one.

            :returns: A :class:`Session` ready to issue authenticated calls.
        """
        token = self._resolve_bearer(aspects=aspects, force_remint=force_remint)

        session = Session()
        session.verify = self._verify_certificate
        session.headers.update({
            "Authorization": "Bearer {}".format(token),
            "Accept": "application/json",
        })

        rtnval = session
        return rtnval

    def _resolve_bearer(self, *, aspects: AspectsTailscale,
                        force_remint: bool) -> str:
        """
            Resolve the bearer token for outbound calls.

            :param aspects: Behaviour-control aspects supplying the OAuth
                refresh margin.
            :param force_remint: When ``True``, force an OAuth re-mint.

            :returns: The bearer token string.
        """
        if self._static_bearer is not None:
            rtnval = self._static_bearer
            return rtnval

        oauth_cred: TailscaleOAuthCredential = self._credential
        margin = aspects.oauth_refresh_margin_seconds
        now_ts = time.time()

        use_cache = False
        if force_remint is False and self._bearer is not None:
            use_cache = self._bearer.is_fresh(margin_seconds=margin, now=now_ts)

        if use_cache is False:
            self._bearer = mint_bearer(credential=oauth_cred,
                                       host_url=self._host_url,
                                       verify_certificate=self._verify_certificate,
                                       now=now_ts)

        rtnval = self._bearer.token
        return rtnval

    def _send(self, *, method: str, leaf: str,
              params: Optional[Dict[str, str]],
              json_body: Optional[Union[Dict[str, Any], list]],
              headers: Optional[Dict[str, str]],
              session: Session, aspects: AspectsTailscale) -> Response:
        """
            Perform the actual HTTP send through the supplied session.

            :param method: HTTP method to invoke.
            :param leaf: API leaf path beginning with ``/``.
            :param params: Optional query-string parameters.
            :param json_body: Optional dict/list serialized as the body.
            :param headers: Optional additional request headers.
            :param session: The session to send through.
            :param aspects: Behaviour-control aspects.

            :returns: The :class:`Response` object from the send.
        """
        call_url = self._format_call_url(leaf)
        send_timeouts = (aspects.connection_timeout, aspects.inactivity_timeout)

        body_bytes: Optional[bytes] = None
        send_headers: Dict[str, str] = {}
        if headers is not None:
            send_headers.update(headers)

        if json_body is not None:
            body_bytes = json.dumps(json_body).encode("utf-8")
            if "Content-Type" not in send_headers:
                send_headers["Content-Type"] = "application/json"

        response: Response = session.request(method=method, url=call_url,
                                             params=params, data=body_bytes,
                                             headers=send_headers,
                                             timeout=send_timeouts,
                                             verify=self._verify_certificate)
        rtnval = response
        return rtnval

    # ------------------------------------------------------------------
    # IVPNControlPlane surface
    # ------------------------------------------------------------------

    def mint_authkey(self, *, reusable: bool, ephemeral: bool,
                     tags: List[str], ttl_seconds: int,
                     aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> str:
        """
            Mint a short-lived authentication key bound to ``tags``.

            :param reusable: Whether the key may be reused across multiple
                node bring-ups.
            :param ephemeral: Whether the resulting node registration is
                ephemeral.
            :param tags: Tags to bind to the key.
            :param ttl_seconds: Requested TTL in seconds; must be > 0.
            :param aspects: Behaviour control for the call.

            :returns: The minted auth-key string.

            :raises: :class:`SemanticError` when ``ttl_seconds`` is not
                positive.
        """
        if ttl_seconds is None:
            raise SemanticError("'ttl_seconds' must be a positive integer.")
        if ttl_seconds <= 0:
            raise SemanticError("'ttl_seconds' must be a positive integer.")

        minted = self._keys.mint(reusable=reusable, ephemeral=ephemeral,
                                 tags=tags, ttl_seconds=ttl_seconds,
                                 aspects=aspects)
        key_value = getattr(minted, "key", None)
        if key_value is None:
            err_msg_lines = ["Tailscale auth-key mint response missing 'key'."]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        rtnval = key_value
        return rtnval

    def list_devices(self, *,
                     aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> List[VPNDeviceRecord]:
        """
            Enumerate devices currently registered in the tailnet.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`VPNDeviceRecord` entries.
        """
        devices = self._devices.list(aspects=aspects)

        rtnval: List[VPNDeviceRecord] = []
        for device in devices:
            record = self.device_to_record(device=device)
            rtnval.append(record)

        return rtnval

    def delete_device(self, *, device_id: str,
                      aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            De-register a device from the tailnet. A missing device is
            treated as already removed (idempotent contract).

            :param device_id: The provider-assigned device identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        self._devices.delete(device_id=device_id, aspects=aspects)
        return

    def apply_acl(self, *, acl_doc: dict,
                  aspects: AspectsTailscale = DEFAULT_TAILSCALE_ASPECTS) -> None:
        """
            Apply a tailnet-wide ACL document.

            :param acl_doc: The ACL payload to apply.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.
        """
        if acl_doc is None:
            raise SemanticError("'acl_doc' must be a dictionary.")

        self._acls.put(acl_doc=acl_doc, aspects=aspects)
        return

    # ------------------------------------------------------------------
    # Adapters
    # ------------------------------------------------------------------

    def device_to_record(self, *, device: TailscaleDevice) -> VPNDeviceRecord:
        """
            Adapt a typed :class:`TailscaleDevice` model into the
            provider-neutral :class:`VPNDeviceRecord` dataclass.

            :param device: The :class:`TailscaleDevice` to adapt.

            :returns: A populated :class:`VPNDeviceRecord`.
        """
        device_id = getattr(device, "id", None)
        node_id = getattr(device, "nodeId", None)
        if device_id is None:
            device_id = node_id
        if device_id is None:
            device_id = ""

        hostname = getattr(device, "hostname", None)
        if hostname is None:
            hostname = ""

        addresses = getattr(device, "addresses", None)
        overlay_address = self._first_cgnat(addresses=addresses)

        raw_tags = getattr(device, "tags", None)
        tags: List[str] = []
        if raw_tags is not None:
            for tag_value in raw_tags:
                tags.append(tag_value)

        os_value = getattr(device, "os", None)
        last_seen = getattr(device, "lastSeen", None)

        rtnval = VPNDeviceRecord(device_id=device_id,
                                 hostname=hostname,
                                 overlay_address=overlay_address,
                                 tags=tags,
                                 os=os_value,
                                 last_seen=last_seen)
        return rtnval

    def _first_cgnat(self, *,
                     addresses: Optional[List[str]]) -> Optional[str]:
        """
            Select the first CGNAT (100.64.0.0/10) IPv4 address from a list.

            :param addresses: A list of address strings, or ``None``.

            :returns: The first matching address, or ``None``.
        """
        if addresses is None:
            rtnval: Optional[str] = None
            return rtnval
        if len(addresses) == 0:
            rtnval = None
            return rtnval

        for addr_str in addresses:
            try:
                addr_obj = ipaddress.ip_address(addr_str)
            except ValueError:
                continue
            if addr_obj.version != 4:
                continue
            if addr_obj in CGNAT_NETWORK:
                rtnval = addr_str
                return rtnval

        rtnval = None
        return rtnval
