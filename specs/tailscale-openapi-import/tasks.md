# Implementation Plan — Tailscale OpenAPI Import

## Codegen Module

- [ ] 1. Create `source/packages/automojo/restclient/tailscale/_codegen/__init__.py`
- [ ] 2. Implement `_codegen/typemap.py` — OpenAPI type/format → Python type with `date-time` → `datetime`
- [ ] 3. Implement `_codegen/emitter.py` — walks `components/schemas/*`, emits one `SchemaObject` subclass per schema
- [ ] 4. Implement `_codegen/import_openapi.py` — fetches + validates + invokes emitter
- [ ] 5. Add deterministic output: stable field ordering, stable file header (no timestamps)

## Spec Storage

- [ ] 6. Create `_spec/` directory with `.gitkeep`
- [ ] 7. Fetch initial OpenAPI document and check in as `_spec/openapi.json`
- [ ] 8. Compute SHA-256 of fetched document, store as `_spec/openapi.sha256`

## Generated Output

- [ ] 9. Run the importer; verify generated `model/*.py` files compile and import
- [ ] 10. Add `model/__init__.py` re-exporting every generated class

## Validation

- [ ] 11. Validator rejects non-OpenAPI-3.x documents with `SemanticError`
- [ ] 12. Fetcher rejects non-200 responses with `ConfigurationError` and does not overwrite checked-in spec

## Tests

- [ ] 13. Fixture-based emitter test (small OpenAPI → golden output diff)
- [ ] 14. Import smoke test for every generated `model/` class
- [ ] 15. Property test: `from_dict(to_dict(x)) == x` for any populated generated class (hypothesis)
- [ ] 16. Property test: JSON round-trip preserves equality (hypothesis)
- [ ] 17. Property test: emitter is deterministic — same input → same output bytes (hypothesis)

## Documentation

- [ ] 18. Add a note in the package README explaining how to regenerate
- [ ] 19. Add a `DO NOT EDIT` header in every generated file with regen instructions
