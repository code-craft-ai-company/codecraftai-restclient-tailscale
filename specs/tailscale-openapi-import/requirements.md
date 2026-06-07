# Requirements

## Introduction

The `tailscale-openapi-import` feature pulls the official Tailscale OpenAPI document
from the Tailscale public docs site and converts it into typed Python model classes
under `source/packages/ccai/restclient/tailscale/model/`. The generated models are
`SchemaObject`-shaped per the `codecraftai-restclient-base` pattern so they integrate
cleanly with the rest of the package. The import is rerun whenever Tailscale ships a
breaking change; the generated output is checked in (not regenerated at install time).

This feature does not author the client class hierarchy — that is the
`tailscale-restclient` feature's responsibility. This feature only produces the
typed payloads.

---

## Requirements

### Requirement 1: Fetch the OpenAPI Document

**User Story:** As a maintainer, I want a single command that fetches the upstream
Tailscale OpenAPI doc, so that re-syncing the package with the upstream API is
mechanical.

#### Acceptance Criteria

1. WHEN the maintainer invokes the import script with no arguments THE SYSTEM SHALL
   fetch the OpenAPI document from the Tailscale-published URL and save it under
   `source/packages/ccai/restclient/tailscale/_spec/openapi.json`.
2. WHEN the upstream URL returns a non-200 status THE SYSTEM SHALL raise a
   `ConfigurationError` with the URL and status code in the message and SHALL NOT
   overwrite the existing checked-in spec.
3. WHEN the upstream URL returns a JSON document that fails OpenAPI 3.x schema
   validation THE SYSTEM SHALL raise a `SemanticError` with the validation failure
   and SHALL NOT overwrite the existing checked-in spec.

### Requirement 2: Generate Typed Model Classes

**User Story:** As a client author, I want every OpenAPI schema to be a Python class
with type-hinted fields, so that consumer code is statically inspectable and
round-trippable.

#### Acceptance Criteria

1. WHEN a schema in the OpenAPI document is an `object` THE SYSTEM SHALL emit one
   Python class per schema under `model/`, named PascalCase with no underscores,
   stored in a file lowercase-no-underscore matching the class name.
2. THE SYSTEM SHALL generate every field as type-hinted with the OpenAPI-declared
   type, mapping `string` → `str`, `integer` → `int`, `boolean` → `bool`, `array` →
   `List[T]`, `object` → the referenced class. WHERE an OpenAPI field has format
   `date-time` THE SYSTEM SHALL emit `datetime.datetime`.
3. WHEN a schema field is marked `required` THE SYSTEM SHALL emit the field without
   a default. IF the field is not required THEN THE SYSTEM SHALL emit the field with
   `Optional[T] = None`.
4. THE SYSTEM SHALL emit each generated class as a `SchemaObject` subclass per the
   `codecraftai-restclient-base` pattern, with `to_dict()` / `from_dict(d)` methods
   verified by round-trip property tests.

### Requirement 3: Round-Trip Property

**User Story:** As a maintainer, I want a runnable proof that the generator does not
lose information, so that a regression in the generator is caught at test time, not
at runtime against a live API.

#### Acceptance Criteria

1. THE SYSTEM SHALL include a hypothesis-based property test asserting that for any
   valid populated instance of any generated model class, `from_dict(to_dict(x)) == x`.
2. THE SYSTEM SHALL include a property test asserting that for any OpenAPI-conformant
   JSON dict matching a schema, parsing into the corresponding model class and
   re-serialising produces a dict that is JSON-equivalent to the input.
