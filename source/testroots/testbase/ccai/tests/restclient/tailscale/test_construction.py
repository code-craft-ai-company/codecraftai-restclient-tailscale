"""
    .. module:: test_construction
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for :class:`TailscaleClient` construction and
                   :class:`IVPNControlPlane` conformance.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai import testbase


from ccai.errors.exceptions import ConfigurationError

from ccai.credentials.basiccredential import BasicCredential

from ccai.interfaces.ivpncontrolplane import IVPNControlPlane

from ccai.restclient.tailscale.tailscaleclient import TailscaleClient
from ccai.restclient.tailscale.apigroups.devicesgroup import DevicesGroup
from ccai.restclient.tailscale.apigroups.keysgroup import KeysGroup
from ccai.restclient.tailscale.apigroups.aclsgroup import AclsGroup
from ccai.restclient.tailscale.apigroups.tailnetsgroup import TailnetsGroup
from ccai.restclient.tailscale.apigroups.dnsgroup import DnsGroup
from ccai.restclient.tailscale.apigroups.posturegroup import PostureGroup

from .testsupport import (
    make_authkey_client, make_oauth_client
)


def test_construct_with_authkey_credential():
    """
        Constructing with an auth-key credential succeeds and stores it as a
        static bearer.
    """
    client = make_authkey_client()
    assert client._static_bearer == "tskey-auth-static-0001"
    assert client.tailnet == "example.com"
    return


def test_construct_with_oauth_credential():
    """
        Constructing with an OAuth credential succeeds without minting a
        bearer eagerly.
    """
    client = make_oauth_client()
    assert client._static_bearer is None
    assert client._bearer is None
    return


def test_construct_with_wrong_credential_raises_configuration_error():
    """
        Constructing with a non-Tailscale credential raises
        :class:`ConfigurationError`.
    """
    bad_credential = BasicCredential(identifier="basic",
                                     categories=["basic"],
                                     username="user",
                                     password="pass")
    with testbase.raises(ConfigurationError):
        TailscaleClient(credential=bad_credential, tailnet="-")
    return


def test_client_is_vpn_control_plane():
    """
        The client satisfies the runtime-checkable
        :class:`IVPNControlPlane` protocol.
    """
    client = make_authkey_client()
    assert isinstance(client, IVPNControlPlane) is True
    return


def test_groups_are_restapigroup_subclasses():
    """
        Each exposed api group is an instance of its dedicated
        ``RestApiGroup`` subclass.
    """
    client = make_authkey_client()
    assert isinstance(client.devices, DevicesGroup) is True
    assert isinstance(client.keys, KeysGroup) is True
    assert isinstance(client.acls, AclsGroup) is True
    assert isinstance(client.tailnets, TailnetsGroup) is True
    assert isinstance(client.dns, DnsGroup) is True
    assert isinstance(client.posture, PostureGroup) is True
    return
