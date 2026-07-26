"""
    .. module:: test_properties
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Hypothesis property tests — URL composition totality,
                   paging completeness/termination, bearer mint-at-most-once
                   per window, and generated-model round-trip.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import List, Optional

import requests_mock as rm_module

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.restclient.tailscale.oauthbearer import OAuthBearer
from ccai.restclient.tailscale.model.tailscaledevice import TailscaleDevice

from ccai.tests.restclient.tailscale.testsupport import (
    TEST_HOST, TEST_TAILNET, make_authkey_client
)


BASE = "https://{}".format(TEST_HOST)
TNET = "/api/v2/tailnet/{}".format(TEST_TAILNET)


# A device-id strategy: non-empty, URL-path-safe segments.
device_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-",
    min_size=1, max_size=24)


@given(device_id=device_id_strategy, constraints={"max_examples": 100})
def test_property_device_url_composition_is_total(device_id: str):
    """
        For any valid device id, the per-device leaf is well-formed: it
        starts with the base, contains no double slash, and ends with the
        device id.
    """
    client = make_authkey_client()
    leaf = client.devices.build_leaf(parts=["device", device_id])
    assert leaf.startswith("/api/v2/device/")
    assert "//" not in leaf
    assert leaf.endswith(device_id)
    return


@given(
    constraints={"max_examples": 100},device_id=device_id_strategy,
       subpath=st.sampled_from(["authorized", "tags", "key"]))
def test_property_nested_device_url_composition_is_total(device_id: str,
                                                         subpath: str):
    """
        For any valid device id and known sub-path, the composed leaf is
        well-formed and matches the OpenAPI path template.
    """
    client = make_authkey_client()
    leaf = client.devices.build_leaf(parts=["device", device_id, subpath])
    assert leaf == "/api/v2/device/{}/{}".format(device_id, subpath)
    return


@given(record_count=st.integers(min_value=0, max_value=60), constraints={"max_examples": 50})
def test_property_iter_visits_every_record_once(record_count: int):
    """
        For any device count, ``devices.iter`` yields exactly that many
        records, each exactly once, and terminates.
    """
    client = make_authkey_client()
    body = {"devices": [{"id": "d{}".format(i), "hostname": "h"}
                        for i in range(record_count)]}
    with rm_module.Mocker() as mock:
        mock.get("{}{}/devices".format(BASE, TNET), json=body)
        seen = list(client.devices.iter())

    seen_ids = [d.id for d in seen]
    assert len(seen_ids) == record_count
    assert len(set(seen_ids)) == record_count
    expected = ["d{}".format(i) for i in range(record_count)]
    assert seen_ids == expected
    return


@given(
    constraints={"max_examples": 50},page_sizes=st.lists(st.integers(min_value=0, max_value=8),
                           min_size=1, max_size=8))
def test_property_cursor_paging_visits_every_record_once(page_sizes: List[int]):
    """
        For any sequence of cursor pages, ``iter_pages_cursor`` visits every
        item exactly once and terminates.
    """
    client = make_authkey_client()
    group = client.devices

    # Build pages: each page carries a slice of a global sequence and a
    # cursor pointing at the next page (None on the last page).
    total = sum(page_sizes)
    sequence = ["item-{}".format(i) for i in range(total)]
    pages = []
    offset = 0
    for index, size in enumerate(page_sizes):
        chunk = sequence[offset:offset + size]
        offset = offset + size
        is_last = index == (len(page_sizes) - 1)
        next_cursor: Optional[str] = None
        if not is_last:
            next_cursor = "cursor-{}".format(index + 1)
        pages.append({"items": chunk, "next": next_cursor})

    by_cursor = {None: pages[0]}
    for index in range(1, len(pages)):
        by_cursor["cursor-{}".format(index)] = pages[index]

    def fetch_page(cursor: Optional[str]) -> dict:
        return by_cursor[cursor]

    visited = list(group.iter_pages_cursor(fetch_page=fetch_page,
                                           aspects=client.aspects))
    assert visited == sequence
    assert len(visited) == total
    return


@given(
    constraints={"max_examples": 80},events=st.lists(
    st.tuples(st.integers(min_value=0, max_value=10000),
              st.booleans()),
    min_size=1, max_size=20))
def test_property_bearer_minted_at_most_once_per_window(events):
    """
        For any sequence of (time-advance, expired-or-not) events, a bearer
        is re-minted only when stale: a fresh bearer is never re-minted.

        This models the cache-decision logic in ``OAuthBearer.is_fresh``:
        once minted at time T with window W, no mint happens again until
        ``now + margin >= T + W``.
    """
    margin = 60.0
    window = 3600.0
    now = 0.0
    bearer: Optional[OAuthBearer] = None
    mint_count = 0
    last_mint_time = -1.0

    for advance, _force in events:
        now = now + float(advance)

        fresh = False
        if bearer is not None:
            fresh = bearer.is_fresh(margin_seconds=margin, now=now)

        if not fresh:
            bearer = OAuthBearer(token="tok", expires_at=now + window)
            mint_count = mint_count + 1
            # A mint must never happen while still inside the previous
            # fresh window.
            if last_mint_time >= 0.0:
                assert (now + margin) >= (last_mint_time + window)
            last_mint_time = now

    # At least one mint occurred and the final bearer is the cached one.
    assert mint_count >= 1
    return


# A populated-device strategy for the model round-trip property.
device_dict_strategy = st.fixed_dictionaries({
    "id": st.text(min_size=1, max_size=16),
    "nodeId": st.text(min_size=1, max_size=16),
    "hostname": st.text(min_size=0, max_size=32),
    "addresses": st.lists(st.sampled_from(["100.64.0.1", "fd7a::1",
                                           "8.8.8.8"]), max_size=4),
    "os": st.sampled_from(["linux", "windows", "macOS"]),
})


@given(data=device_dict_strategy, constraints={"max_examples": 100})
def test_property_generated_model_roundtrip(data):
    """
        For any populated device dict, ``from_dict(to_dict(x)) == x`` holds
        on the generated :class:`TailscaleDevice` model.
    """
    instance = TailscaleDevice.from_dict(data)
    restored = TailscaleDevice.from_dict(instance.to_dict())
    assert restored == instance
    return
