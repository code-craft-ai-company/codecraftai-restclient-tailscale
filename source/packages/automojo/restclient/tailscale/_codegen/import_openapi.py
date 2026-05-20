"""
    .. module:: import_openapi
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Maintainer-facing script that fetches the Tailscale
                   OpenAPI document, validates it, and regenerates the
                   typed model classes under ``model/``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import hashlib
import os

from typing import Any, Dict

import requests
import yaml

from automojo.errors.exceptions import ConfigurationError, SemanticError

from automojo.restclient.tailscale._codegen.emitter import (
    emit_all_schemas, emit_model_init
)


OPENAPI_URL = "https://api.tailscale.com/api/v2?outputOpenapiSchema=true"

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_DIR = os.path.join(PACKAGE_ROOT, "_spec")
MODEL_DIR = os.path.join(PACKAGE_ROOT, "model")
SPEC_FILE = os.path.join(SPEC_DIR, "openapi.json")
SHA_FILE = os.path.join(SPEC_DIR, "openapi.sha256")


def fetch_openapi_document(*, url: str = OPENAPI_URL) -> str:
    """
        Fetch the upstream Tailscale OpenAPI document text.

        :param url: The upstream document URL.

        :returns: The raw document text.

        :raises: :class:`ConfigurationError` when the upstream URL returns a
            non-200 status.
    """
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        err_msg_lines = ["Failed to fetch the Tailscale OpenAPI document."]
        err_msg_lines.append("URL: {}".format(url))
        err_msg_lines.append("STATUS: {}".format(response.status_code))
        err_msg = os.linesep.join(err_msg_lines)
        raise ConfigurationError(err_msg)

    rtnval = response.text
    return rtnval


def validate_openapi_document(*, document_text: str) -> Dict[str, Any]:
    """
        Parse and validate an OpenAPI document text against OpenAPI 3.x.

        :param document_text: The raw document text (YAML or JSON).

        :returns: The parsed document dictionary.

        :raises: :class:`SemanticError` when the document is not a valid
            OpenAPI 3.x document.
    """
    try:
        parsed = yaml.safe_load(document_text)
    except yaml.YAMLError as yamlerr:
        err_msg_lines = ["Tailscale OpenAPI document failed to parse."]
        err_msg_lines.append("DETAIL: {}".format(yamlerr))
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg) from None

    if not isinstance(parsed, dict):
        raise SemanticError("Tailscale OpenAPI document is not a mapping.")

    version = parsed.get("openapi")
    if version is None or not str(version).startswith("3."):
        err_msg_lines = ["Document is not an OpenAPI 3.x document."]
        err_msg_lines.append("FOUND VERSION: {}".format(version))
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    try:
        from openapi_spec_validator import validate as _validate_spec
        _validate_spec(parsed)
    except ImportError:
        # The validator is an optional maintainer-side dependency. The
        # version check above is the minimum gate when it is absent.
        pass
    except Exception as valerr:
        err_msg_lines = ["Tailscale OpenAPI document failed schema validation."]
        err_msg_lines.append("DETAIL: {}".format(valerr))
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg) from None

    rtnval = parsed
    return rtnval


def regenerate_models(*, document: Dict[str, Any]) -> int:
    """
        Regenerate every model file from a validated OpenAPI document.

        :param document: The parsed and validated OpenAPI document.

        :returns: The count of model files written.
    """
    components = document.get("components")
    if components is None:
        raise SemanticError("OpenAPI document has no 'components' section.")

    schemas = components.get("schemas")
    if schemas is None:
        raise SemanticError("OpenAPI document has no 'components/schemas'.")

    emitted = emit_all_schemas(schemas=schemas)

    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    written = 0
    for module_name in sorted(emitted.keys()):
        _, source_text = emitted[module_name]
        target_path = os.path.join(MODEL_DIR, "{}.py".format(module_name))
        with open(target_path, "w", encoding="utf-8") as model_file:
            model_file.write(source_text)
        written = written + 1

    init_source = emit_model_init(emitted=emitted)
    init_path = os.path.join(MODEL_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as init_file:
        init_file.write(init_source)

    rtnval = written
    return rtnval


def main() -> None:
    """
        Run the full fetch/validate/regenerate import flow.

        :returns: ``None``.
    """
    document_text = fetch_openapi_document()
    document = validate_openapi_document(document_text=document_text)

    if not os.path.exists(SPEC_DIR):
        os.makedirs(SPEC_DIR)

    with open(SPEC_FILE, "w", encoding="utf-8") as spec_file:
        spec_file.write(document_text)

    digest = hashlib.sha256(document_text.encode("utf-8")).hexdigest()
    with open(SHA_FILE, "w", encoding="utf-8") as sha_file:
        sha_file.write(digest)
        sha_file.write(os.linesep)

    count = regenerate_models(document=document)

    print("Regenerated {} Tailscale model files.".format(count))
    return


if __name__ == "__main__":
    main()
