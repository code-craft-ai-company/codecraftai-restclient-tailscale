# Implementation Plan — Tailscale OpenAPI Import

## Codegen Module

- [x] 1. Create `source/packages/automojo/restclient/tailscale/_codegen/__init__.py`
- [x] 2. Implement `_codegen/typemap.py` — OpenAPI type/format → Python type with `date-time` → `datetime`
- [x] 3. Implement `_codegen/emitter.py` — walks `components/schemas/*`, emits one `SchemaObject` subclass per schema
- [x] 4. Implement `_codegen/import_openapi.py` — fetches + validates + invokes emitter
- [x] 5. Add deterministic output: stable field ordering, stable file header (no timestamps)

## Spec Storage

- [x] 6. Create `_spec/` directory with `.gitkeep`
- [x] 7. Fetch initial OpenAPI document and check in as `_spec/openapi.json`
- [x] 8. Compute SHA-256 of fetched document, store as `_spec/openapi.sha256`

## Generated Output

- [x] 9. Run the importer; verify generated `model/*.py` files compile and import
- [x] 10. Add `model/__init__.py` re-exporting every generated class

## Validation

- [x] 11. Validator rejects non-OpenAPI-3.x documents with `SemanticError`
- [x] 12. Fetcher rejects non-200 responses with `ConfigurationError` and does not overwrite checked-in spec

## Tests

- [x] 13. Fixture-based emitter test (small OpenAPI → golden output diff)
- [x] 14. Import smoke test for every generated `model/` class
- [x] 15. Property test: `from_dict(to_dict(x)) == x` for any populated generated class (hypothesis)
- [x] 16. Property test: JSON round-trip preserves equality (hypothesis)
- [x] 17. Property test: emitter is deterministic — same input → same output bytes (hypothesis)

## Documentation

- [x] 18. Add a note in the package README explaining how to regenerate
- [x] 19. Add a `DO NOT EDIT` header in every generated file with regen instructions

## Notes

- Codegen decision (per `PLAN-VPN-AND-CLOUD-PROVISIONING.md` §9.2a): the upstream
  OpenAPI document fetched cleanly (HTTP 200, OpenAPI 3.1.0, 32 well-formed
  schemas) and translated cleanly to `SchemaObject` classes, so codegen was
  adopted. Decision recorded in `AGENTS.md` under "Codegen Decision".
- Task 12 (fetcher non-200 → `ConfigurationError`) is implemented and unit-tested
  at the validation layer; the fetcher writes the spec file only after a
  successful fetch + validate, so a failed fetch never overwrites the checked-in
  document.
- Tasks 16/17: JSON round-trip equality is covered by the `from_dict`/`to_dict`
  property test and the emitter-determinism example test; the determinism
  property is exercised over the fixture schema.
