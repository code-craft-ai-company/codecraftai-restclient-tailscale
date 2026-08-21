"""
    .. module:: test_controlplane
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for the :class:`IVPNControlPlane` surface of
                   :class:`TailscaleClient` and the model adapters.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai import testbase


import requests_mock as rm_module

from ccai.errors.exceptions import SemanticError

from ccai.interfaces.ivpncontrolplane import VPNDeviceRecord

from ccai.restclient.tailscale.model.tailscaledevice import TailscaleDevice

from .testsupport import (
    TEST_HOST, TEST_TAILNET, make_authkey_client
)


BASE = "https://{}".format(TEST_HOST)
TNET = "/api/v2/tailnet/{}".format(TEST_TAILNET)


def test_mint_authkey_delegates_to_keys_group():
    """
        ``mint_authkey`` delegates to ``keys.mint`` and returns the key
        string.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.post("{}{}/keys".format(BASE, TNET),
                  json={"id": "k1", "key": "tskey-auth-out"})
        key = client.mint_authkey(reusable=False, ephemeral=True,
                                  tags=["tag:lab"], ttl_seconds=600)

    assert key == "tskey-auth-out"
    return


def test_mint_authkey_rejects_non_positive_ttl():
    """
        ``mint_authkey`` rejects a non-positive TTL.
    """
    client = make_authkey_client()
    with testbase.raises(SemanticError):
        client.mint_authkey(reusable=False, ephemeral=True, tags=[],
                            ttl_seconds=-1)
    return


def test_list_devices_returns_vpn_device_records():
    """
        ``list_devices`` adapts every device to a
        :class:`VPNDeviceRecord`.
    """
    client = make_authkey_client()
    body = {"devices": [
        {"id": "d1", "hostname": "host-a",
         "addresses": ["100.64.0.5", "fd7a::1"],
         "tags": ["tag:lab"], "os": "linux", "lastSeen": "2025-01-01T00:00:00Z"},
    ]}
    with rm_module.Mocker() as mock:
        mock.get("{}{}/devices".format(BASE, TNET), json=body)
        records = client.list_devices()

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, VPNDeviceRecord) is True
    assert record.device_id == "d1"
    assert record.hostname == "host-a"
    assert record.overlay_address == "100.64.0.5"
    assert record.tags == ["tag:lab"]
    assert record.os == "linux"
    return


def test_delete_device_delegates():
    """
        ``delete_device`` delegates to ``devices.delete``.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.delete("{}/api/v2/device/d1".format(BASE), status_code=200)
        client.delete_device(device_id="d1")
        assert mock.last_request.method == "DELETE"
    return


def test_apply_acl_delegates():
    """
        ``apply_acl`` delegates to ``acls.put``.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.post("{}{}/acl".format(BASE, TNET), json={"acls": []})
        client.apply_acl(acl_doc={"acls": [{"action": "accept"}]})
        assert mock.last_request.method == "POST"
    return


def test_apply_acl_rejects_none():
    """
        ``apply_acl`` rejects a ``None`` document.
    """
    client = make_authkey_client()
    with testbase.raises(SemanticError):
        client.apply_acl(acl_doc=None)
    return


def test_device_to_record_falls_back_to_node_id():
    """
        The device adapter uses ``nodeId`` when ``id`` is absent.
    """
    client = make_authkey_client()
    device = TailscaleDevice(nodeId="n123", hostname="h", addresses=[])
    record = client.device_to_record(device=device)
    assert record.device_id == "n123"
    return


def test_device_to_record_no_cgnat_address():
    """
        The device adapter yields ``None`` overlay address when no CGNAT
        IPv4 address is present.
    """
    client = make_authkey_client()
    device = TailscaleDevice(id="d1", hostname="h",
                             addresses=["8.8.8.8", "fd7a::1"])
    record = client.device_to_record(device=device)
    assert record.overlay_address is None
    return
