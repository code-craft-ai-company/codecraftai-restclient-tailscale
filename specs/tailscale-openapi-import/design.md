# Design

## Overview

The `tailscale-openapi-import` feature is realised as a maintainer-facing import
script plus generated output. The script lives at
`source/packages/automojo/restclient/tailscale/_codegen/import_openapi.py` and is
invoked by hand when the upstream Tailscale OpenAPI document changes. The script:

1. Fetches the OpenAPI document via HTTPS GET.
2. Validates it against OpenAPI 3.x.
3. Walks every `components/schemas/<Name>` entry and emits one Python file per schema
   under `source/packages/automojo/restclient/tailscale/model/`.
4. Emits an `__init__.py` re-exporting every generated class.

Generated output is **checked in**. CI does not regenerate. This is deliberate: the
generated code is the source of truth for what shape the client code can use, and
checking it in lets reviewers see API drift in PR diffs.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Maintainer                                                │
│   $ python -m automojo.restclient.tailscale._codegen.import_openapi
│                                                           │
│   ┌─────────────────────────────────────────────────┐    │
│   │ Fetcher (requests.get)                          │    │
│   │   → openapi.json under _spec/                   │    │
│   └─────────────────────────────────────────────────┘    │
│             │                                             │
│   ┌─────────▼────────────────────────────────────────┐   │
│   │ Validator (openapi-spec-validator)               │   │
│   └─────────┬────────────────────────────────────────┘   │
│             │                                             │
│   ┌─────────▼────────────────────────────────────────┐   │
│   │ Emitter (walks components/schemas/*)             │   │
│   │   → one *.py per schema in model/                │   │
│   │   → __init__.py re-exports                       │   │
│   └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## Data Model

Each emitted class is a `SchemaObject` subclass (from `automojo.restclient.base.schemaobject`):

```python
class TailscaleDevice(SchemaObject):
    """
        Auto-generated from Tailscale OpenAPI schema `Device`.

        DO NOT EDIT BY HAND. Run `python -m automojo.restclient.tailscale._codegen.import_openapi`
        to regenerate.
    """

    name: str
    id: str
    addresses: List[str]
    last_seen: Optional[datetime]
    tags: Optional[List[str]] = None
    # ...
```

The generated file carries a `DO NOT EDIT` warning in the docstring and a hash of the
upstream schema snippet in a module-level constant so CI can detect manual edits.

## Module Layout

```
source/packages/automojo/restclient/tailscale/
  _spec/
    openapi.json          # checked-in upstream document
    openapi.sha256        # checksum
  _codegen/
    __init__.py
    import_openapi.py     # the maintainer-facing import script
    emitter.py            # SchemaObject emitter
    typemap.py            # OpenAPI type → Python type mapping
  model/
    __init__.py           # re-exports
    tailscaledevice.py    # one file per schema (generated)
    ...
```

## See Also

- [tailscale-restclient](../tailscale-restclient/design.md)
- `automojo-restclient-base` — `SchemaObject`, `SchemaField`

## Testing Strategy

**Example-based tests:**
- Run the emitter against a small fixture OpenAPI document; assert the generated files
  match a golden output.
- Smoke-test that the checked-in generated `model/` files import without error.
- Smoke-test that every generated class round-trips through `from_dict(to_dict(x))`.

**Property tests (hypothesis):**
- For any populated instance of any generated `SchemaObject` subclass, `from_dict(to_dict(x)) == x`.
- For any OpenAPI-conformant dict matching a schema, parsing then re-serialising
  produces a JSON-equivalent dict.
- The emitter is deterministic: running it twice on the same input produces
  byte-identical output.
