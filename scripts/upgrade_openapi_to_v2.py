#!/usr/bin/env python3
"""Upgrade docs OpenAPI specs from v1 X-API-KEY to v2 public Bearer API."""

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "config" / "routes.oas.json"
YAML_PATH = ROOT / "config" / "openapi.yaml"

NEW_SINGLE = "https://api.verifyafrica.io/api/v2/public/verifications/requests/"
OLD_DETAIL_BASE = "https://api.verifyafrica.io/api/v2/public/verifications/requests/"

INFO_DESCRIPTION = """\
Identity verification, compliance screening, and government registry checks across Africa.

## Authentication

All endpoints require a tenant API key as a Bearer token:

```
Authorization: Bearer VA-your_api_key_here
```

Do not send `X-API-KEY`. Tenant context comes from the API key — no `X-TENANT-ID` header is required.

## API Sections

- **Create** — Submit one verification via `POST /api/v2/public/verifications/requests/`
- **Detail** — Retrieve a verification via `GET /api/v2/public/verifications/requests/{verification_id}/detail/`

Public create requests always run in **direct (offsite)** mode. Hosted/link (`onsite`) flows are not available on this API.

## Response format

Success responses use:

```json
{ "success": true, "message": "...", "data": { ... } }
```

Error responses use:

```json
{ "success": false, "message": "...", "errors": ["..."] }
```

## Base URL

`https://api.verifyafrica.io`
"""


def strip_is_test(obj):
    if isinstance(obj, dict):
        obj.pop("is_test", None)
        for value in obj.values():
            strip_is_test(value)
    elif isinstance(obj, list):
        for item in obj:
            strip_is_test(item)


def strip_method_type(obj):
    if isinstance(obj, dict):
        obj.pop("method_type", None)
        for value in obj.values():
            strip_method_type(value)
    elif isinstance(obj, list):
        for item in obj:
            strip_method_type(item)


def rewrite_base_urls(obj):
    if isinstance(obj, dict):
        for key, value in list(obj.items()):
            if key == "baseUrl" and isinstance(value, str):
                if "/api/verifications/bulk/" in value:
                    obj[key] = NEW_SINGLE
                elif "/api/verifications/requests/" in value:
                    obj[key] = NEW_SINGLE
            else:
                rewrite_base_urls(value)
    elif isinstance(obj, list):
        for item in obj:
            rewrite_base_urls(item)


def update_security(obj):
    if isinstance(obj, dict):
        if "security" in obj and isinstance(obj["security"], list):
            obj["security"] = [{"BearerAuth": []}]
        for value in obj.values():
            update_security(value)
    elif isinstance(obj, list):
        for item in obj:
            update_security(item)


def transform(spec: dict) -> dict:
    spec = copy.deepcopy(spec)

    spec["info"]["version"] = "2.0.0"
    spec["info"]["title"] = "Verify Africa Public API"
    spec["info"]["description"] = INFO_DESCRIPTION
    spec["security"] = [{"BearerAuth": []}]

    # Keep only single tags
    tags = [t for t in spec.get("tags", []) if not str(t.get("name", "")).startswith("bulk-")]
    for tag in tags:
        desc = tag.get("description", "")
        tag["description"] = desc.replace(" — single verification requests.", " — create verification requests.")
        tag["description"] = tag["description"].replace("Bulk government", "Government")
    spec["tags"] = tags

    # Single tag group only
    single_group = next(
        (g for g in spec.get("x-tagGroups", []) if g.get("name") == "Single"),
        None,
    )
    if single_group:
        single_group["name"] = "Verifications"
        single_group["tags"] = [t for t in single_group.get("tags", []) if not str(t).startswith("bulk-")]
        spec["x-tagGroups"] = [single_group]
    else:
        spec.pop("x-tagGroups", None)

    # Paths: drop bulk, rename single paths
    new_paths: dict = {}
    for path, methods in spec.get("paths", {}).items():
        if "/bulk/" in path:
            continue

        new_path = path.replace("/api/verifications/requests/", "/api/v2/public/verifications/requests/")
        op = methods.get("post") or next(iter(methods.values()), None)
        if op:
            # Drop bulk references from descriptions
            if "description" in op and isinstance(op["description"], str):
                lines = [
                    line
                    for line in op["description"].splitlines()
                    if "bulk" not in line.lower() and "hosted page" not in line.lower()
                ]
                op["description"] = "\n".join(lines).strip()
                if "direct" not in op["description"].lower() and "offsite" not in op["description"].lower():
                    op["description"] = (
                        (op["description"] + "\n\n" if op["description"] else "")
                        + "Public API creates always use direct (offsite) mode."
                    ).strip()

            # Response codes: prefer 201 for create
            responses = op.get("responses", {})
            if "200" in responses and "201" not in responses:
                responses["201"] = responses.pop("200")
                responses["201"]["description"] = "Verification created successfully"
            for code in ("207", "422"):
                responses.pop(code, None)

            # Schema example cleanup happens below via strip_*
            content = (
                op.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
            )
            schema = content.get("schema", {})
            if isinstance(schema, dict) and "properties" in schema:
                schema["properties"].pop("is_test", None)
                schema["properties"].pop("method_type", None)
                required = schema.get("required")
                if isinstance(required, list):
                    schema["required"] = [r for r in required if r not in ("is_test", "method_type")]

            # Replace response schema refs
            for resp in responses.values():
                if not isinstance(resp, dict):
                    continue
                app = resp.get("content", {}).get("application/json", {})
                if "schema" in app:
                    app["schema"] = {"$ref": "#/components/schemas/V2SuccessResponse"}
                examples = app.get("examples", {})
                if isinstance(examples, dict):
                    for ex in examples.values():
                        if isinstance(ex, dict) and "value" in ex and isinstance(ex["value"], dict):
                            # wrap old payload into v2 envelope if needed
                            value = ex["value"]
                            if "success" not in value:
                                data = value.get("data", value)
                                ex["value"] = {
                                    "success": True,
                                    "message": "Verification request created successfully.",
                                    "data": data if isinstance(data, dict) else {"result": data},
                                }

        rewrite_base_urls(methods)
        strip_is_test(methods)
        strip_method_type(methods)
        update_security(methods)
        new_paths[new_path] = methods

    # Add detail endpoint
    new_paths["/api/v2/public/verifications/requests/{verification_id}/detail/"] = {
        "get": {
            "summary": "Get verification detail",
            "description": (
                "Retrieve a verification request belonging to the API key's tenant, "
                "including optional Shufti proof metadata when available."
            ),
            "operationId": "public-verification-detail",
            "tags": ["single-identity-verification"],
            "security": [{"BearerAuth": []}],
            "parameters": [
                {
                    "name": "verification_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                    "description": "Verification request ID returned from create.",
                }
            ],
            "responses": {
                "200": {
                    "description": "Verification request retrieved successfully",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/V2SuccessResponse"},
                            "examples": {
                                "success": {
                                    "summary": "Successful detail response",
                                    "value": {
                                        "success": True,
                                        "message": "Verification request retrieved successfully.",
                                        "data": {
                                            "id": "06a4f688-4de4-70ad-8000-ada533c461f4",
                                            "verification_type": "ng_bvn_verification",
                                            "status": "SUCCESS",
                                            "input_data": {"bvn": "22222222222"},
                                            "response_data": {},
                                            "by_api": True,
                                            "api_key_id": "06a4f688-4a96-7027-8000-089b60351c6c",
                                            "proofs_available": False,
                                            "proofs": {},
                                        },
                                    },
                                }
                            },
                        }
                    },
                },
                "401": {"description": "Unauthorized - Invalid or missing Bearer API key"},
                "404": {"description": "Not Found - Verification does not exist for this tenant"},
                "500": {"description": "Internal Server Error"},
            },
            "x-zuplo-route": {
                "corsPolicy": "none",
                "handler": {
                    "export": "urlForwardHandler",
                    "module": "$import(@zuplo/runtime)",
                    "options": {"baseUrl": OLD_DETAIL_BASE},
                },
            },
        }
    }

    spec["paths"] = new_paths

    components = spec.setdefault("components", {})
    components["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": (
                "Tenant API key from the VerifyAfrica dashboard (`VA-…`). "
                "Send as `Authorization: Bearer <api_key>`. Do not use `X-API-KEY`."
            ),
        }
    }
    schemas = components.setdefault("schemas", {})
    schemas.pop("BulkVerificationRequest", None)
    schemas.pop("BulkVerificationResponse", None)
    schemas["V2SuccessResponse"] = {
        "type": "object",
        "required": ["success", "message", "data"],
        "properties": {
            "success": {"type": "boolean", "example": True},
            "message": {"type": "string"},
            "data": {
                "type": "object",
                "description": "Verification request payload.",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "verification_type": {"type": "string"},
                    "status": {"type": "string"},
                    "input_data": {"type": "object"},
                    "response_data": {"type": "object"},
                    "cost_charged": {"type": "string"},
                    "currency": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "reference": {"type": "string"},
                    "source": {"type": "string"},
                    "by_api": {"type": "boolean", "nullable": True},
                    "api_key_id": {"type": "string", "format": "uuid", "nullable": True},
                    "link": {"type": "object", "nullable": True},
                    "email_sent_at": {"type": "string", "format": "date-time", "nullable": True},
                    "proofs_available": {"type": "boolean"},
                    "proofs": {"type": "object"},
                },
            },
        },
    }
    schemas["V2ErrorResponse"] = {
        "type": "object",
        "required": ["success", "message", "errors"],
        "properties": {
            "success": {"type": "boolean", "example": False},
            "message": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
        },
    }
    # Keep VerificationResponse for backwards refs but point to v2 shape
    schemas["VerificationResponse"] = {"$ref": "#/components/schemas/V2SuccessResponse"}

    strip_is_test(spec)
    strip_method_type(spec)
    return spec


def main() -> None:
    with JSON_PATH.open() as f:
        spec = json.load(f)

    # Allow re-run only from original v1 shape; if already upgraded, skip.
    sample_path = next(iter(spec.get("paths", {})), "")
    if sample_path.startswith("/api/v2/public/"):
        print("OpenAPI already looks upgraded; skipping transform.")
        return

    updated = transform(spec)

    with JSON_PATH.open("w") as f:
        json.dump(updated, f, indent=2)
        f.write("\n")

    # Zudoku uses routes.oas.json; keep openapi.yaml as the same JSON document
    # (valid OpenAPI) so editors stay in sync without requiring PyYAML.
    with YAML_PATH.open("w") as f:
        json.dump(updated, f, indent=2)
        f.write("\n")

    print(f"Updated {JSON_PATH}")
    print(f"Updated {YAML_PATH}")
    print(f"Paths: {len(updated['paths'])}")


if __name__ == "__main__":
    main()
