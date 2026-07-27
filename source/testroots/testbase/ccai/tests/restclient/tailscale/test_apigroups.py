"""
    .. module:: test_apigroups
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for each Tailscale api-group method — URL
                   composition, body shape, and header presence — with all
                   HTTP traffic mocked via ``requests-mock``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai import testbase


import json

import requests_mock as rm_module

from ccai.errors.exceptions import SemanticError

from ccai.restclient.tailscale.exceptions import (
    TailscaleApiError, TailscaleAuthError, TailscaleNotFoundError,
    TailscaleRateLimitError, TailscaleServerError
)

from ccai.restclient.tailscale.model.tailscaledevice import TailscaleDevice
from ccai.restclient.tailscale.model.tailscalekey import TailscaleKey

from ccai.tests.restclient.tailscale.testsupport import (
    TEST_HOST, TEST_TAILNET, make_authkey_client
)


BASE = "https://{}".format(TEST_HOST)
TNET = "/api/v2/tailnet/{}".format(TEST_TAILNET)


def test_devices_list_url_and_parsing():
    """
        ``devices.list`` composes the tailnet devices URL and parses every
        entry into a :class:`TailscaleDevice`.
    """
    client = make_authkey_client()
    body = {"devices": [{"id": "d1", "hostname": "h1",
                         "addresses": ["100.64.0.1"]},
                        {"id": "d2", "hostname": "h2", "addresses": []}]}
    with rm_module.Mocker() as mock:
        mock.get("{}{}/devices".format(BASE, TNET), json=body)
        devices = client.devices.list()
        assert mock.last_request.path == "{}/devices".format(TNET)
        assert mock.last_request.qs.get("fields") == ["all"]

    assert len(devices) == 2
    assert isinstance(devices[0], TailscaleDevice) is True
    assert devices[0].id == "d1"
    return


def test_devices_iter_visits_every_record():
    """
        ``devices.iter`` yields every record exactly once.
    """
    client = make_authkey_client()
    body = {"devices": [{"id": "d{}".format(i), "hostname": "h"}
                        for i in range(5)]}
    with rm_module.Mocker() as mock:
        mock.get("{}{}/devices".format(BASE, TNET), json=body)
        ids = [d.id for d in client.devices.iter()]

    assert ids == ["d0", "d1", "d2", "d3", "d4"]
    return


def test_devices_get_url():
    """
        ``devices.get`` composes the per-device URL.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}/api/v2/device/d1".format(BASE),
                 json={"id": "d1", "hostname": "h1"})
        device = client.devices.get(device_id="d1")
        assert mock.last_request.path == "/api/v2/device/d1"

    assert device.id == "d1"
    return


def test_devices_delete_treats_404_as_success():
    """
        ``devices.delete`` treats a 404 as already-removed.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.delete("{}/api/v2/device/gone".format(BASE), status_code=404)
        client.devices.delete(device_id="gone")
        assert mock.last_request.method == "DELETE"
    return


def test_devices_delete_raises_on_500():
    """
        ``devices.delete`` raises a typed :class:`TailscaleServerError` on a
        non-2xx, non-404 response.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.delete("{}/api/v2/device/d1".format(BASE), status_code=500,
                    text="boom")
        with testbase.raises(TailscaleServerError) as excinfo:
            client.devices.delete(device_id="d1")
        assert excinfo.value.status_code == 500
        assert "boom" in excinfo.value.response_body
    return


def test_devices_list_403_raises_auth_error():
    """
        ``devices.list`` reclassifies a 403 into a :class:`TailscaleAuthError`.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/devices".format(BASE, TNET), status_code=403,
                 text='{"message":"forbidden"}')
        with testbase.raises(TailscaleAuthError) as excinfo:
            client.devices.list()
        assert excinfo.value.status_code == 403
        assert "forbidden" in excinfo.value.response_body
        assert isinstance(excinfo.value, TailscaleApiError)
    return


def test_devices_list_401_raises_auth_error():
    """
        ``devices.list`` reclassifies a 401 into a :class:`TailscaleAuthError`.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/devices".format(BASE, TNET), status_code=401,
                 text="unauthorized")
        with testbase.raises(TailscaleAuthError):
            client.devices.list()
    return


def test_keys_get_404_raises_not_found_error():
    """
        ``keys.get`` reclassifies a 404 into a :class:`TailscaleNotFoundError`.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/keys/missing".format(BASE, TNET), status_code=404,
                 text="not found")
        with testbase.raises(TailscaleNotFoundError) as excinfo:
            client.keys.get(key_id="missing")
        assert excinfo.value.status_code == 404
    return


def test_devices_list_429_raises_rate_limit_error():
    """
        ``devices.list`` reclassifies a 429 into a
        :class:`TailscaleRateLimitError`.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/devices".format(BASE, TNET), status_code=429,
                 text="slow down")
        with testbase.raises(TailscaleRateLimitError) as excinfo:
            client.devices.list()
        assert excinfo.value.status_code == 429
    return


def test_devices_delete_empty_id_raises():
    """
        ``devices.delete`` rejects an empty device id.
    """
    client = make_authkey_client()
    with testbase.raises(SemanticError):
        client.devices.delete(device_id="")
    return


def test_devices_set_authorized_body():
    """
        ``devices.set_authorized`` posts the authorized flag.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.post("{}/api/v2/device/d1/authorized".format(BASE),
                  status_code=200)
        client.devices.set_authorized(device_id="d1", authorized=True)
        sent = json.loads(mock.last_request.body)
        assert sent == {"authorized": True}
    return


def test_devices_set_tags_body():
    """
        ``devices.set_tags`` posts the replacement tag list.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.post("{}/api/v2/device/d1/tags".format(BASE), status_code=200)
        client.devices.set_tags(device_id="d1", tags=["tag:lab", "tag:ci"])
        sent = json.loads(mock.last_request.body)
        assert sent == {"tags": ["tag:lab", "tag:ci"]}
    return


def test_devices_set_key_expiry_disabled_body():
    """
        ``devices.set_key_expiry_disabled`` posts the key-expiry flag.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.post("{}/api/v2/device/d1/key".format(BASE), status_code=200)
        client.devices.set_key_expiry_disabled(device_id="d1", disabled=True)
        sent = json.loads(mock.last_request.body)
        assert sent == {"keyExpiryDisabled": True}
    return


def test_keys_list_url_and_parsing():
    """
        ``keys.list`` composes the tailnet keys URL and parses entries.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/keys".format(BASE, TNET),
                 json={"keys": [{"id": "k1"}, {"id": "k2"}]})
        keys = client.keys.list()
        assert mock.last_request.path == "{}/keys".format(TNET)

    assert len(keys) == 2
    assert isinstance(keys[0], TailscaleKey) is True
    return


def test_keys_iter_visits_every_record():
    """
        ``keys.iter`` yields every key exactly once.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/keys".format(BASE, TNET),
                 json={"keys": [{"id": "k{}".format(i)} for i in range(3)]})
        ids = [k.id for k in client.keys.iter()]

    assert ids == ["k0", "k1", "k2"]
    return


def test_keys_get_url():
    """
        ``keys.get`` composes the per-key URL.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/keys/k1".format(BASE, TNET), json={"id": "k1"})
        key = client.keys.get(key_id="k1")
        assert mock.last_request.path == "{}/keys/k1".format(TNET)

    assert key.id == "k1"
    return


def test_keys_mint_body_shape():
    """
        ``keys.mint`` builds the nested capabilities request body.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.post("{}{}/keys".format(BASE, TNET),
                  json={"id": "k1", "key": "tskey-auth-minted"})
        key = client.keys.mint(reusable=True, ephemeral=False,
                               tags=["tag:lab"], ttl_seconds=900)
        sent = json.loads(mock.last_request.body)
        create = sent["capabilities"]["devices"]["create"]
        assert create["reusable"] is True
        assert create["ephemeral"] is False
        assert create["preauthorized"] is True
        assert create["tags"] == ["tag:lab"]
        assert sent["expirySeconds"] == 900

    assert key.key == "tskey-auth-minted"
    return


def test_keys_mint_rejects_non_positive_ttl():
    """
        ``keys.mint`` rejects a non-positive TTL.
    """
    client = make_authkey_client()
    with testbase.raises(SemanticError):
        client.keys.mint(reusable=False, ephemeral=True, tags=[],
                          ttl_seconds=0)
    return


def test_keys_delete_treats_404_as_success():
    """
        ``keys.delete`` treats a 404 as already-removed.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.delete("{}{}/keys/gone".format(BASE, TNET), status_code=404)
        client.keys.delete(key_id="gone")
    return


def test_acls_get_returns_document_and_etag():
    """
        ``acls.get`` returns the ACL document and the ETag header.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/acl".format(BASE, TNET), json={"acls": []},
                 headers={"ETag": "etag-1"})
        document, etag = client.acls.get()

    assert document == {"acls": []}
    assert etag == "etag-1"
    return


def test_acls_put_sends_if_match_when_etag_present():
    """
        ``acls.put`` attaches an ``If-Match`` header when an ETag is given.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.post("{}{}/acl".format(BASE, TNET), json={"acls": []})
        client.acls.put(acl_doc={"acls": []}, etag="etag-1")
        assert mock.last_request.headers.get("If-Match") == "etag-1"
    return


def test_acls_put_omits_if_match_when_no_etag():
    """
        ``acls.put`` omits the ``If-Match`` header when no ETag is given.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.post("{}{}/acl".format(BASE, TNET), json={"acls": []})
        client.acls.put(acl_doc={"acls": []})
        assert mock.last_request.headers.get("If-Match") is None
    return


def test_tailnets_get_settings_url():
    """
        ``tailnets.get_settings`` composes the settings URL.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/settings".format(BASE, TNET),
                 json={"devicesApprovalOn": True})
        settings = client.tailnets.get_settings()
        assert mock.last_request.path == "{}/settings".format(TNET)

    assert settings.devicesApprovalOn is True
    return


def test_tailnets_update_settings_body():
    """
        ``tailnets.update_settings`` PATCHes the settings body.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.patch("{}{}/settings".format(BASE, TNET), status_code=200)
        client.tailnets.update_settings(settings={"devicesApprovalOn": False})
        assert mock.last_request.method == "PATCH"
        sent = json.loads(mock.last_request.body)
        assert sent == {"devicesApprovalOn": False}
    return


def test_dns_get_nameservers():
    """
        ``dns.get_nameservers`` returns the nameserver list.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/dns/nameservers".format(BASE, TNET),
                 json={"dns": ["1.1.1.1", "8.8.8.8"]})
        nameservers = client.dns.get_nameservers()

    assert nameservers == ["1.1.1.1", "8.8.8.8"]
    return


def test_dns_set_nameservers_body():
    """
        ``dns.set_nameservers`` posts the replacement nameserver list.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.post("{}{}/dns/nameservers".format(BASE, TNET), json={})
        client.dns.set_nameservers(nameservers=["9.9.9.9"])
        sent = json.loads(mock.last_request.body)
        assert sent == {"dns": ["9.9.9.9"]}
    return


def test_dns_get_search_paths():
    """
        ``dns.get_search_paths`` returns the search-path list.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/dns/searchpaths".format(BASE, TNET),
                 json={"searchPaths": ["lab.example.com"]})
        paths = client.dns.get_search_paths()

    assert paths == ["lab.example.com"]
    return


def test_dns_get_preferences():
    """
        ``dns.get_preferences`` returns the preferences object.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/dns/preferences".format(BASE, TNET),
                 json={"magicDNS": True})
        prefs = client.dns.get_preferences()

    assert prefs == {"magicDNS": True}
    return


def test_posture_list_integrations():
    """
        ``posture.list_integrations`` parses the integration list.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/posture/integrations".format(BASE, TNET),
                 json={"integrations": [{"id": "pi1"}, {"id": "pi2"}]})
        integrations = client.posture.list_integrations()

    assert len(integrations) == 2
    assert integrations[0].id == "pi1"
    return


def test_posture_list_signing_nodes():
    """
        ``posture.list_signing_nodes`` returns the signing-node list.
    """
    client = make_authkey_client()
    url = "{}{}/devices/posture/integrations/signing-nodes".format(BASE, TNET)
    with rm_module.Mocker() as mock:
        mock.get(url, json={"signingNodes": [{"nodeId": "n1"}]})
        nodes = client.posture.list_signing_nodes()

    assert nodes == [{"nodeId": "n1"}]
    return


def test_authorization_header_present():
    """
        Every request carries the static bearer ``Authorization`` header.
    """
    client = make_authkey_client()
    with rm_module.Mocker() as mock:
        mock.get("{}{}/devices".format(BASE, TNET), json={"devices": []})
        client.devices.list()
        auth = mock.last_request.headers.get("Authorization")
        assert auth == "Bearer tskey-auth-static-0001"
    return
