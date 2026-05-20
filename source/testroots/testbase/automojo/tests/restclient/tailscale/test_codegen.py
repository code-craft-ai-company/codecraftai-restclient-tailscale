"""
    .. module:: test_codegen
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Tests for the OpenAPI import codegen — emitter
                   determinism, validation gates, and generated-model
                   smoke tests.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import importlib

import pytest

from automojo.errors.exceptions import SemanticError

from automojo.restclient.tailscale._codegen.emitter import (
    class_name_for_schema, emit_all_schemas, emit_schema_module
)
from automojo.restclient.tailscale._codegen.typemap import python_type_for_schema
from automojo.restclient.tailscale._codegen.import_openapi import (
    validate_openapi_document
)

import automojo.restclient.tailscale.model as model_pkg


FIXTURE_SCHEMA = {
    "type": "object",
    "description": "A fixture schema.",
    "required": ["name"],
    "properties": {
        "name": {"type": "string"},
        "count": {"type": "integer"},
        "active": {"type": "boolean"},
        "created": {"type": "string", "format": "date-time"},
        "labels": {"type": "array", "items": {"type": "string"}},
    },
}


def test_class_name_for_schema():
    """
        Schema names map to ``Tailscale``-prefixed PascalCase class names.
    """
    assert class_name_for_schema(schema_name="Device") == "TailscaleDevice"
    assert class_name_for_schema(schema_name="Dns_Search_Paths") == "TailscaleDnsSearchPaths"
    return


def test_typemap_scalar_and_format():
    """
        The type map handles scalars, the ``date-time`` format, and arrays.
    """
    assert python_type_for_schema(schema={"type": "string"}) == "str"
    assert python_type_for_schema(schema={"type": "integer"}) == "int"
    assert python_type_for_schema(schema={"type": "boolean"}) == "bool"
    assert python_type_for_schema(
        schema={"type": "string", "format": "date-time"}) == "datetime"
    assert python_type_for_schema(
        schema={"type": "array", "items": {"type": "string"}}) == "List[str]"
    return


def test_typemap_unknown_type_raises():
    """
        An unmapped OpenAPI type raises :class:`SemanticError`.
    """
    with pytest.raises(SemanticError):
        python_type_for_schema(schema={"type": "frobnicate"})
    return


def test_emitter_is_deterministic():
    """
        Emitting the same schema twice produces byte-identical source.
    """
    _, _, source_a = emit_schema_module(schema_name="Widget",
                                        schema=FIXTURE_SCHEMA)
    _, _, source_b = emit_schema_module(schema_name="Widget",
                                        schema=FIXTURE_SCHEMA)
    assert source_a == source_b
    return


def test_emitter_fixture_golden_shape():
    """
        The fixture schema emits a well-formed ``SchemaObject`` subclass
        with required field first and a ``date-time`` field typed as
        ``datetime``.
    """
    class_name, module_name, source = emit_schema_module(
        schema_name="Widget", schema=FIXTURE_SCHEMA)
    assert class_name == "TailscaleWidget"
    assert module_name == "tailscalewidget"
    assert "class TailscaleWidget(SchemaObject):" in source
    assert "name = Field(str, required=True" in source
    assert "created = Field(Optional[datetime]" in source
    # Required field is emitted before optional fields.
    name_idx = source.index("name = Field")
    count_idx = source.index("count = Field")
    assert name_idx < count_idx
    return


def test_emit_all_schemas_skips_non_objects():
    """
        ``emit_all_schemas`` only emits object-shaped schemas.
    """
    schemas = {
        "Widget": FIXTURE_SCHEMA,
        "LogType": {"type": "string", "enum": ["a", "b"]},
    }
    emitted = emit_all_schemas(schemas=schemas)
    assert "tailscalewidget" in emitted
    assert "tailscalelogtype" not in emitted
    return


def test_validate_rejects_non_openapi3():
    """
        The validator rejects a document that is not OpenAPI 3.x.
    """
    with pytest.raises(SemanticError):
        validate_openapi_document(document_text="openapi: 2.0\ninfo: {}\n")
    return


def test_validate_rejects_non_mapping():
    """
        The validator rejects a document that is not a mapping.
    """
    with pytest.raises(SemanticError):
        validate_openapi_document(document_text="- just\n- a\n- list\n")
    return


def test_generated_models_import_and_roundtrip():
    """
        Every generated model class imports and round-trips an empty
        instance through ``from_dict(to_dict(x))``.
    """
    assert len(model_pkg.__all__) > 0
    for class_name in model_pkg.__all__:
        model_cls = getattr(model_pkg, class_name)
        instance = model_cls()
        restored = model_cls.from_dict(instance.to_dict())
        assert restored == instance
    return


def test_generated_device_module_has_do_not_edit_header():
    """
        The generated device module carries the DO NOT EDIT header.
    """
    module = importlib.import_module(
        "automojo.restclient.tailscale.model.tailscaledevice")
    assert "DO NOT EDIT BY HAND" in module.__doc__
    return
