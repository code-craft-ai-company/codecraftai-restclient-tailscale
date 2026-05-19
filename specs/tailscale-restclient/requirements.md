# Requirements

## Introduction

The `tailscale-restclient` feature is the public face of the
`automojo-restclient-tailscale` package: a `RestClientBase` subclass that exposes
Tailscale's `api.tailscale.com/api/v2/` endpoints through typed Python methods. It
consumes the generated models from `tailscale-openapi-import`. It implements the
`IVPNControlPlane` Protocol from `automojo-interfaces` so consumers (notably the
M3 control-plane shim in `automojo-interop/vpn/tailscale/`) can substitute it
transparently.

---

## Requirements

### Requirement 1: Construct from Credential

**User Story:** As a consumer, I want to construct the client by passing a typed
credential, so that auth handling is a closed problem inside the client.

#### Acceptance Criteria

1. WHEN the consumer constructs `TailscaleClient(host=..., credential=<TailscaleOAuthCredential>)` THE SYSTEM SHALL accept the credential and lazily mint a bearer token on first call.
2. WHEN the consumer constructs `TailscaleClient(host=..., credential=<TailscaleAuthKeyCredential>)` THE SYSTEM SHALL accept the credential and use it as a static bearer token without OAuth exchange.
3. IF the credential is any other `BaseCredential` subclass THEN THE SYSTEM SHALL raise `ConfigurationError` at construction time.

### Requirement 2: IVPNControlPlane Conformance

**User Story:** As a consumer, I want the client to satisfy `isinstance(client, IVPNControlPlane)`, so that it can be substituted anywhere a control plane is expected.

#### Acceptance Criteria

1. THE SYSTEM SHALL implement every method on `IVPNControlPlane`: `mint_authkey`, `list_devices`, `delete_device`, `apply_acl`.
2. THE SYSTEM SHALL pass `isinstance(client, IVPNControlPlane)` via the runtime-checkable Protocol.

### Requirement 3: API Group Surface

**User Story:** As a consumer, I want every Tailscale API endpoint exposed as a typed Python method on a logical group, so that I don't compose URLs by hand.

#### Acceptance Criteria

1. THE SYSTEM SHALL expose API groups as properties on `TailscaleClient`: `devices`, `keys`, `acls`, `tailnets`, `dns`, `posture`.
2. THE SYSTEM SHALL implement each group as a `RestApiGroup` subclass.
3. THE SYSTEM SHALL accept `aspects: AspectsRest = DEFAULT_TAILSCALE_ASPECTS` on every behaviour-bearing call.
4. WHERE the upstream endpoint returns a paged list THE SYSTEM SHALL expose both a `list(...)` method returning the first page and an `iter(...)` method that walks all pages via `iter_pages_cursor` from the base.

### Requirement 4: OAuth Token Lifecycle

**User Story:** As a consumer using OAuth credentials, I want bearer tokens minted lazily, cached for their TTL, and refreshed on 401, so that the OAuth dance is invisible.

#### Acceptance Criteria

1. WHEN a `TailscaleOAuthCredential` is in use and the cached bearer is missing THE SYSTEM SHALL mint a new bearer via the OAuth `client_credentials` flow.
2. WHILE a cached bearer is unexpired THE SYSTEM SHALL reuse it across calls.
3. IF an API call returns 401 THEN THE SYSTEM SHALL mint a new bearer once and retry the original call exactly once.
4. IF the retry also returns 401 THEN THE SYSTEM SHALL raise `HttpForbiddenError` and SHALL NOT loop.
