# Implementation Plan — Tailscale REST Client

## Aspects + Auth

- [x] 1. Create `aspectstailscale.py` — `AspectsTailscale(AspectsRest)` + `DEFAULT_TAILSCALE_ASPECTS`
- [x] 2. Create `oauthbearer.py` — `OAuthBearer` dataclass + `mint_bearer(credential, session, aspects)` helper
- [x] 3. Implement 401 → mint-once → retry handler (one retry only; second 401 raises `HttpForbiddenError`)

## Client Construction

- [x] 4. Create `tailscaleclient.py` — `TailscaleClient(RestClientBase)`
- [x] 5. Constructor accepts `TailscaleOAuthCredential` (lazy bearer) or `TailscaleAuthKeyCredential` (static bearer)
- [x] 6. Constructor rejects any other `BaseCredential` with `ConfigurationError`
- [x] 7. Expose `devices` / `keys` / `acls` / `tailnets` / `dns` / `posture` as properties returning group instances

## API Groups

- [x] 8. `apigroups/devicesgroup.py` — `list`, `iter`, `get`, `delete`, `set_authorized`, `set_tags`, `set_key_expiry_disabled`
- [x] 9. `apigroups/keysgroup.py` — `list`, `iter`, `get`, `mint`, `delete`
- [x] 10. `apigroups/aclsgroup.py` — `get`, `put` (with `If-Match` ETag support)
- [x] 11. `apigroups/tailnetsgroup.py` — settings get/update
- [x] 12. `apigroups/dnsgroup.py` — nameservers, preferences, search paths
- [x] 13. `apigroups/posturegroup.py` — integrations + signing nodes

## IVPNControlPlane Conformance

- [x] 14. Implement `mint_authkey(*, reusable, ephemeral, tags, ttl_seconds, aspects)` delegating to `keys.mint`
- [x] 15. Implement `list_devices(*, aspects)` delegating to `devices.list`; adapt `TailscaleDevice` → `VPNDeviceRecord`
- [x] 16. Implement `delete_device(*, device_id, aspects)` delegating to `devices.delete`
- [x] 17. Implement `apply_acl(*, acl_doc, aspects)` delegating to `acls.put`
- [x] 18. Verify `isinstance(client, IVPNControlPlane)` at runtime in a unit test

## Tests

- [x] 19. Example tests for each api-group method (URL composition, body shape, header presence)
- [x] 20. OAuth lifecycle tests (lazy mint, cache, 401-retry, double-401-raise)
- [x] 21. `IVPNControlPlane` isinstance test
- [x] 22. Adapter tests (`VPNDeviceRecord` ↔ `TailscaleDevice` round-trip)
- [x] 23. Property test: URL composition totality (hypothesis)
- [x] 24. Property test: paging visits every record exactly once + terminates (hypothesis)
- [x] 25. Property test: bearer minted ≤ once per expiry window (hypothesis)

## M3 Shim

- [ ] 26. **DEFERRED** — After this package is publishable, edit `codecraftai-interop/vpn/tailscale/tailscalecontrolplane.py` to re-export `TailscaleClient as TailscaleControlPlane` with a `DeprecationWarning`. Deferred because this M3b work item is scoped to the `codecraftai-restclient-tailscale` repository only; the shim lands in a separate change against the `codecraftai-interop` repository. `TailscaleClient` is API-compatible at the wire level with the M3 `TailscaleControlPlane` (`mint_authkey`, `list_devices`, `delete_device`, `apply_acl`, `isinstance(..., IVPNControlPlane)`), so the shim is a one-line re-export when that change is made.
