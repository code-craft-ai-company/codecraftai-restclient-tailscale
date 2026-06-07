"""
    .. module:: typemap
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that maps OpenAPI ``type``/``format`` declarations
                   onto Python type expressions used by the model emitter.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os

from typing import Any, Dict

from ccai.errors.exceptions import SemanticError


SCALAR_TYPE_MAP: Dict[str, str] = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}


def python_type_for_schema(*, schema: Dict[str, Any]) -> str:
    """
        Resolve a single OpenAPI schema fragment to a Python type expression
        usable as a ``Field`` ``field_type`` argument.

        :param schema: An OpenAPI schema fragment dictionary.

        :returns: A Python type-expression string (for example ``"str"`` or
            ``"List[str]"``).

        :raises: :class:`SemanticError` when the fragment declares a type
            that the emitter has no mapping for.
    """
    if schema is None:
        rtnval = "Any"
        return rtnval

    ref_value = schema.get("$ref")
    if ref_value is not None:
        # Cross-schema references are emitted as quoted forward-ref strings.
        # The ``Field`` descriptor accepts ``Any`` for ``field_type`` so a
        # string class name is a valid, import-order-independent type tag.
        ref_name = ref_value.rsplit("/", 1)[-1]
        rtnval = "'Tailscale{}'".format(ref_name)
        return rtnval

    declared_type = schema.get("type")

    if declared_type is None:
        # allOf / oneOf / untyped fragments degrade to Any so the emitter
        # never produces an unimportable file.
        rtnval = "Any"
        return rtnval

    if isinstance(declared_type, list):
        # OpenAPI 3.1 allows a list of types (commonly ["string", "null"]).
        non_null = [entry for entry in declared_type if entry != "null"]
        if len(non_null) == 1:
            inner_schema = dict(schema)
            inner_schema["type"] = non_null[0]
            rtnval = python_type_for_schema(schema=inner_schema)
            return rtnval
        rtnval = "Any"
        return rtnval

    if declared_type == "array":
        item_schema = schema.get("items")
        item_type = python_type_for_schema(schema=item_schema)
        rtnval = "List[{}]".format(item_type)
        return rtnval

    if declared_type == "object":
        rtnval = "Dict[str, Any]"
        return rtnval

    if declared_type in SCALAR_TYPE_MAP:
        if declared_type == "string":
            declared_format = schema.get("format")
            if declared_format == "date-time":
                rtnval = "datetime"
                return rtnval
        rtnval = SCALAR_TYPE_MAP[declared_type]
        return rtnval

    err_msg_lines = ["Unmapped OpenAPI type encountered by the emitter."]
    err_msg_lines.append("TYPE: {}".format(declared_type))
    err_msg = os.linesep.join(err_msg_lines)
    raise SemanticError(err_msg)
