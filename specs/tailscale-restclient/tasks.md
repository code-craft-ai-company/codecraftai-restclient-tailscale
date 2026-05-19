# Implementation Plan — Tailscale REST Client

## Aspects + Auth

- [ ] 1. Create `aspectstailscale.py` — `AspectsTailscale(AspectsRest)` + `DEFAULT_TAILSCALE_ASPECTS`
- [ ] 2. Create `oauthbearer.py` — `OAuthBearer` dataclass + `mint_bearer(credential, session, aspects)` helper
- [ ] 3. Implement 401 → mint-once → retry handler (one retry only; second 401 raises `HttpForbiddenError`)

## Client Construction

- [ ] 4. Create `tailscaleclient.py` — `TailscaleClient(RestClientBase)`
- [ ] 5. Constructor accepts `TailscaleOAuthCredential` (lazy bearer) or `TailscaleAuthKeyCredential` (static bearer)
- [ ] 6. Constructor rejects any other `BaseCredential` with `ConfigurationError`
- [ ] 7. Expose `devices` / `keys` / `acls` / `tailnets` / `dns` / `posture` as properties returning group instances

## API Groups

- [ ] 8. `apigroups/devicesgroup.py` — `list`, `iter`, `get`, `delete`, `set_authorized`, `set_tags`, `set_key_expiry_disabled`
- [ ] 9. `apigroups/keysgroup.py` — `list`, `iter`, `get`, `mint`, `delete`
- [ ] 10. `apigroups/aclsgroup.py` — `get`, `put` (with `If-Match` ETag support)
- [ ] 11. `apigroups/tailnetsgroup.py` — settings get/update
- [ ] 12. `apigroups/dnsgroup.py` — nameservers, preferences, search paths
- [ ] 13. `apigroups/posturegroup.py` — integrations + signing nodes

## IVPNControlPlane Conformance

- [ ] 14. Implement `mint_authkey(*, reusable, ephemeral, tags, ttl_seconds, aspects)` delegating to `keys.mint`
- [ ] 15. Implement `list_devices(*, aspects)` delegating to `devices.list`; adapt `TailscaleDevice` → `VPNDeviceRecord`
- [ ] 16. Implement `delete_device(*, device_id, aspects)` delegating to `devices.delete`
- [ ] 17. Implement `apply_acl(*, acl_doc, aspects)` delegating to `acls.put`
- [ ] 18. Verify `isinstance(client, IVPNControlPlane)` at runtime in a unit test

## Tests

- [ ] 19. Example tests for each api-group method (URL composition, body shape, header presence)
- [ ] 20. OAuth lifecycle tests (lazy mint, cache, 401-retry, double-401-raise)
- [ ] 21. `IVPNControlPlane` isinstance test
- [ ] 22. Adapter tests (`VPNDeviceRecord` ↔ `TailscaleDevice` round-trip)
- [ ] 23. Property test: URL composition totality (hypothesis)
- [ ] 24. Property test: paging visits every record exactly once + terminates (hypothesis)
- [ ] 25. Property test: bearer minted ≤ once per expiry window (hypothesis)

## M3 Shim

- [ ] 26. After this package is publishable, edit `automojo-interop/vpn/tailscale/tailscalecontrolplane.py` to re-export `TailscaleClient as TailscaleControlPlane` with a `DeprecationWarning` emitted once per import path per process
