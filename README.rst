=====================================
Code Craft AI RestClient - Tailscale
=====================================

The ``codecraftai-restclient-tailscale`` package is a typed, aspect-driven REST client for the Tailscale public API (``api.tailscale.com/api/v2/``). It is built on top of ``codecraftai-restclient-base`` and consumes credentials from ``codecraftai-credentials`` (``TailscaleAuthKeyCredential``, ``TailscaleOAuthCredential``). The package implements the ``IVPNControlPlane`` Protocol declared in ``codecraftai-foundations``, so any consumer that expects a control-plane today can substitute this client transparently.

The implementation landed in Milestone M3b of the VPN/cloud-provisioning plan. See the ``specs/`` folder for the Kiro-style requirements, design, and task documentation that drove that work.

Regenerating the OpenAPI Models
===============================

The typed model classes under ``source/packages/ccai/restclient/tailscale/model/`` are generated from the official Tailscale OpenAPI document. They are checked in and carry a ``DO NOT EDIT BY HAND`` header. To re-sync them after an upstream API change:

.. code-block:: bash

   PYTHONPATH=source/packages python -m ccai.restclient.tailscale._codegen.import_openapi

The importer fetches the document, validates it is OpenAPI 3.x, refreshes ``_spec/openapi.json`` plus its SHA-256 sidecar, and regenerates every ``model/*.py`` file.

Highlights (planned)
====================

- ``TailscaleClient(RestClientBase)`` exposing api groups for ``devices``, ``keys``, ``acls``, ``tailnets``, ``dns``, and ``posture``.
- ``IVPNControlPlane`` Protocol conformance: ``mint_authkey``, ``list_devices``, ``delete_device``, ``apply_acl``.
- OAuth bearer-token lifecycle with lazy mint, caching, and 401-triggered single retry.
- Optional OpenAPI-driven typed model generation under ``model/`` (re-evaluated per the codegen rule in the workspace-level ``PLAN-VPN-AND-CLOUD-PROVISIONING.md`` §9.2a — if generator output is not clean, the client is hand-authored instead).
- Replaces the M3-landed ``codecraftai-interop/vpn/tailscale/tailscalecontrolplane.py``, which becomes a re-export shim for one release cycle after this package ships.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/ccai/restclient/tailscale/`` - Package source code (lands in M3b).
- ``source/testroots/testbase/ccai/tests/restclient/tailscale/`` - TestBase test roots (lands in M3b).
- ``specs/`` - Requirements, design, and task documentation (Kiro-style).
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-environment

Running Tests
=============

Tests land in Milestone M3b. Once source code is in place:

.. code-block:: bash

   source .venv/bin/activate
   testbase testing run --root ./source/testroots/testbase --includes=testbase.ccai.tests

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
- Codegen decision rule: workspace ``PLAN-VPN-AND-CLOUD-PROVISIONING.md`` §9.2a
