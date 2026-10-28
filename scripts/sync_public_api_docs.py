#!/usr/bin/env python3
"""Sync public OpenAPI with backend public API surface.

Updates docs/config/routes.oas.json and docs/config/openapi.yaml:
- Test + production servers
- TTL enum includes 1440
- Facial screening: verification_mode image_only|video_only + face.age
- Mixed verification public routes
- Batch webhook event names
- Info description lists all public URL families
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "config" / "routes.oas.json"
YAML_PATH = ROOT / "config" / "openapi.yaml"

TTL_ENUM = [15, 30, 60, 120, 240, 1440]
FACE_MODE_ENUM = ["image_only", "video_only"]
MIXED_TAG = "mixed-verification"
def _error_response(description: str) -> dict:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/Error Response"},
            }
        },
    }


COMMON_ERROR_RESPONSES = {
    "400": _error_response("Bad Request — validation failed or invalid parameters."),
    "401": _error_response("Unauthorized — missing or invalid API key."),
    "403": _error_response("Forbidden — tenant KYC incomplete, product unavailable, or insufficient wallet balance."),
    "404": _error_response("Not Found — resource does not exist for this tenant."),
    "500": _error_response("Internal Server Error."),
}


def walk(obj, fn):
    fn(obj)
    if isinstance(obj, dict):
        for value in obj.values():
            walk(value, fn)
    elif isinstance(obj, list):
        for value in obj:
            walk(value, fn)


def ensure_servers(spec: dict) -> None:
    spec["servers"] = [
        {"url": "https://api.verifyafrica.io", "description": "Production"},
        {"url": "https://test.api.verifyafrica.io", "description": "Test"},
    ]


def fix_ttl_enums(spec: dict) -> int:
    updated = 0

    def _fix(node):
        nonlocal updated
        if not isinstance(node, dict):
            return
        enum = node.get("enum")
        if enum == [15, 30, 60, 120, 240]:
            node["enum"] = list(TTL_ENUM)
            desc = node.get("description")
            if isinstance(desc, str) and "1440" not in desc:
                node["description"] = (
                    desc.rstrip(".")
                    + ". Allowed: 15, 30, 60, 120, 240, or 1440 (24 hours)."
                )
            updated += 1

    walk(spec, _fix)
    return updated


def fix_facial_screening(spec: dict) -> None:
    path = "/api/v2/public/verifications/requests/facial_screening/"
    post = spec.get("paths", {}).get(path, {}).get("post")
    if not isinstance(post, dict):
        return

    schema = (
        post.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    face = (
        schema.get("properties", {})
        .get("input_data", {})
        .get("properties", {})
        .get("face", {})
    )
    if not isinstance(face, dict):
        return

    face.setdefault("required", [])
    if "verification_mode" not in face["required"]:
        face["required"] = ["verification_mode", *face["required"]]

    props = face.setdefault("properties", {})
    props["verification_mode"] = {
        "type": "string",
        "enum": list(FACE_MODE_ENUM),
        "description": (
            "Required in both modes. Must be `image_only` or `video_only` "
            "(must match `proof` media type in direct mode)."
        ),
        "example": "image_only",
    }
    props["age"] = {
        "type": "object",
        "description": (
            "Optional age gate. When set, both `min` and `max` are required. "
            "`min` must be at least 16."
        ),
        "properties": {
            "min": {"type": "string", "example": "16", "description": "Minimum age (inclusive). ≥ 16."},
            "max": {"type": "string", "example": "80", "description": "Maximum age (inclusive)."},
        },
    }
    props.setdefault(
        "check_duplicate_request",
        {
            "type": "boolean",
            "default": False,
            "description": "Both modes. `true` to flag duplicate faces. Defaults to `false`.",
        },
    )

    # Fix examples under facial_screening only.
    examples = (
        post.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("examples", {})
    )
    if isinstance(examples, dict):
        for example in examples.values():
            value = example.get("value") if isinstance(example, dict) else None
            if not isinstance(value, dict):
                continue
            face_ex = (value.get("input_data") or {}).get("face")
            if isinstance(face_ex, dict) and face_ex.get("verification_mode") in (None, "any"):
                face_ex["verification_mode"] = "image_only"


def ensure_tags(spec: dict) -> None:
    tags = spec.setdefault("tags", [])
    by_name = {t.get("name"): t for t in tags if isinstance(t, dict)}
    if MIXED_TAG not in by_name:
        tags.append(
            {
                "name": MIXED_TAG,
                "description": (
                    "Multi-step hosted verification: templates, sessions, step submit, "
                    "and tenant availability catalog."
                ),
                "x-displayName": "Mixed Verification",
            }
        )
    groups = spec.setdefault("x-tagGroups", [])
    names = {g.get("name") for g in groups if isinstance(g, dict)}
    if "Mixed Verification" not in names:
        # Insert before Webhooks when present.
        insert_at = next(
            (i for i, g in enumerate(groups) if isinstance(g, dict) and g.get("name") == "Webhooks"),
            len(groups),
        )
        groups.insert(insert_at, {"name": "Mixed Verification", "tags": [MIXED_TAG]})


def _success_envelope(data_schema: dict, message: str, status_code: str = "200") -> dict:
    return {
        status_code: {
            "description": message,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["success", "message", "data"],
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "message": {"type": "string", "example": message},
                            "data": data_schema,
                        },
                    }
                }
            },
        }
    }


def mixed_paths() -> dict:
    step_config = {
        "type": "object",
        "additionalProperties": True,
        "description": (
            "Optional per-step defaults merged into child `input_data` at session start. "
            "Unknown keys are rejected. See Mixed Verification docs for allowed keys by type."
        ),
    }
    step_object = {
        "type": "object",
        "required": ["type", "order"],
        "properties": {
            "type": {
                "type": "string",
                "description": (
                    "Verification type for this step. Any product except "
                    "`risk_assessment` and `mixed_verification`."
                ),
                "example": "id_document",
            },
            "order": {"type": "integer", "minimum": 1, "example": 1},
            "config": step_config,
        },
    }
    steps_payload = {
        "type": "object",
        "required": ["steps"],
        "properties": {
            "steps": {
                "type": "object",
                "additionalProperties": step_object,
                "description": "Map of step UUID → step definition.",
            }
        },
    }
    template_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "is_active": {"type": "boolean"},
            "is_custom": {"type": "boolean"},
            "legacy_unsupported": {"type": "boolean"},
            "steps": steps_payload,
            "verifications": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ordered list of step types (derived from steps).",
            },
            "available": {
                "type": "boolean",
                "description": "Whether this template can be started for the current tenant.",
            },
            "reasons": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Structured unavailability reasons when `available` is false.",
            },
        },
    }
    session_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "status": {
                "type": "string",
                "enum": ["PENDING", "PROCESSING", "SUCCESS", "FAILED", "PARTIAL", "ERROR", "ABANDONED"],
            },
            "email": {"type": "string", "format": "email"},
            "reference": {"type": "string", "nullable": True},
            "ttl_minutes": {"type": "integer", "enum": TTL_ENUM},
            "expires_at": {"type": "string", "format": "date-time", "nullable": True},
            "verification_url": {
                "type": "string",
                "format": "uri",
                "description": "Hosted `/new-verify` capture URL for the customer.",
            },
            "link": {
                "type": "object",
                "nullable": True,
                "properties": {"url": {"type": "string", "format": "uri"}},
            },
            "steps": {"type": "array", "items": {"type": "object"}},
        },
    }

    security = [{"BearerAuth": []}]
    base = "/api/v2/public/verifications/mixed-verifications"

    availability = {
        "get": {
            "tags": [MIXED_TAG],
            "operationId": "public-mixed-availability",
            "summary": "Mixed verification availability",
            "description": (
                "Catalog of which mixed step types (and related products) are available "
                "for the API-key tenant, including structured disable reasons."
            ),
            "security": security,
            "responses": {
                **_success_envelope(
                    {"type": "object", "additionalProperties": True},
                    "Mixed verification availability retrieved.",
                ),
                **COMMON_ERROR_RESPONSES,
            },
        }
    }

    templates = {
        "get": {
            "tags": [MIXED_TAG],
            "operationId": "public-mixed-templates-list",
            "summary": "List mixed verification templates",
            "description": (
                "Lists active platform templates and this tenant's custom templates "
                "(excludes legacy unsupported journeys)."
            ),
            "security": security,
            "responses": {
                **_success_envelope(
                    {"type": "array", "items": template_schema},
                    "Mixed verification templates retrieved.",
                ),
                **COMMON_ERROR_RESPONSES,
            },
        },
        "post": {
            "tags": [MIXED_TAG],
            "operationId": "public-mixed-templates-create",
            "summary": "Create mixed verification template",
            "description": (
                "Create a tenant-owned custom template with ordered steps and optional "
                "per-step `config`."
            ),
            "security": security,
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string", "example": "KYC + AML"},
                                "description": {"type": "string"},
                                "is_active": {"type": "boolean", "default": True},
                                "steps": steps_payload,
                                "verifications": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Legacy ordered type list when `steps` is omitted.",
                                },
                            },
                        },
                        "examples": {
                            "with_steps": {
                                "summary": "Steps with per-step config",
                                "value": {
                                    "name": "KYC + AML",
                                    "description": "Passport then AML",
                                    "is_active": True,
                                    "steps": {
                                        "steps": {
                                            "550e8400-e29b-41d4-a716-446655440000": {
                                                "type": "id_document",
                                                "order": 1,
                                                "config": {
                                                    "document": {"supported_types": ["passport"]},
                                                    "collect": {"dob": True},
                                                },
                                            },
                                            "6ba7b810-9dad-11d1-80b4-00c04fd430c8": {
                                                "type": "aml_screening",
                                                "order": 2,
                                                "config": {
                                                    "filters": {
                                                        "filters": ["sanction", "pep"],
                                                        "match_score": 70,
                                                        "rca_search": True,
                                                        "alias_search": True,
                                                    }
                                                },
                                            },
                                        }
                                    },
                                },
                            }
                        },
                    }
                },
            },
            "responses": {
                **_success_envelope(template_schema, "Mixed verification template created.", "201"),
                **COMMON_ERROR_RESPONSES,
            },
        },
    }

    template_detail = {
        "get": {
            "tags": [MIXED_TAG],
            "operationId": "public-mixed-templates-detail",
            "summary": "Get mixed verification template",
            "security": security,
            "parameters": [
                {
                    "name": "template_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                }
            ],
            "responses": {
                **_success_envelope(template_schema, "Mixed verification template retrieved."),
                **COMMON_ERROR_RESPONSES,
            },
        },
        "patch": {
            "tags": [MIXED_TAG],
            "operationId": "public-mixed-templates-update",
            "summary": "Update mixed verification template",
            "description": "Only tenant-owned custom templates can be updated. Platform templates are read-only.",
            "security": security,
            "parameters": [
                {
                    "name": "template_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                }
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "is_active": {"type": "boolean"},
                                "steps": steps_payload,
                                "verifications": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        }
                    }
                },
            },
            "responses": {
                **_success_envelope(template_schema, "Mixed verification template updated."),
                **COMMON_ERROR_RESPONSES,
            },
        },
    }

    sessions = {
        "post": {
            "tags": [MIXED_TAG],
            "operationId": "public-mixed-sessions-start",
            "summary": "Start mixed verification session",
            "description": (
                "Start a hosted multi-step session from `template_id` **or** inline "
                "`steps` / `verifications`. Returns a capture URL. Each step is billed "
                "when submitted."
            ),
            "security": security,
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["email"],
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                                "template_id": {"type": "string", "format": "uuid"},
                                "reference": {"type": "string"},
                                "ttl": {
                                    "type": "integer",
                                    "enum": TTL_ENUM,
                                    "default": 60,
                                    "description": "Hosted link lifetime in minutes.",
                                },
                                "steps": steps_payload,
                                "verifications": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Legacy ordered type list when not using template_id/steps.",
                                },
                            },
                        },
                        "examples": {
                            "from_template": {
                                "summary": "Start from template",
                                "value": {
                                    "template_id": "06adb17a-0000-0000-0000-000000000001",
                                    "email": "customer@example.com",
                                    "reference": "order-123",
                                    "ttl": 60,
                                },
                            }
                        },
                    }
                },
            },
            "responses": {
                **_success_envelope(session_schema, "Mixed verification session started.", "201"),
                **COMMON_ERROR_RESPONSES,
            },
        }
    }

    session_detail = {
        "get": {
            "tags": [MIXED_TAG],
            "operationId": "public-mixed-sessions-detail",
            "summary": "Get mixed verification session",
            "security": security,
            "parameters": [
                {
                    "name": "session_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                }
            ],
            "responses": {
                **_success_envelope(session_schema, "Mixed verification session retrieved."),
                **COMMON_ERROR_RESPONSES,
            },
        }
    }

    step_submit = {
        "post": {
            "tags": [MIXED_TAG],
            "operationId": "public-mixed-sessions-step-submit",
            "summary": "Submit mixed verification step",
            "description": (
                "Submit one step of an in-progress session. Returns `202` and processes "
                "asynchronously. Wallet debit happens per step on submit."
            ),
            "security": security,
            "parameters": [
                {
                    "name": "session_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                },
                {
                    "name": "step_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                    "description": "Step UUID from the template/session steps map.",
                },
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "additionalProperties": True,
                            "description": "Step-specific capture payload (fields vary by step type).",
                        }
                    }
                },
            },
            "responses": {
                **_success_envelope(
                    {"type": "object", "additionalProperties": True},
                    "Mixed verification step accepted.",
                    "202",
                ),
                **COMMON_ERROR_RESPONSES,
            },
        }
    }

    return {
        f"{base}/availability/": availability,
        f"{base}/templates/": templates,
        f"{base}/templates/{'{template_id}'}/": template_detail,
        f"{base}/sessions/": sessions,
        f"{base}/sessions/{'{session_id}'}/": session_detail,
        f"{base}/sessions/{'{session_id}'}/steps/{'{step_id}'}/": step_submit,
    }


def ensure_mixed_paths(spec: dict) -> int:
    paths = spec.setdefault("paths", {})
    added = 0
    for key, value in mixed_paths().items():
        if key not in paths:
            paths[key] = value
            added += 1
        else:
            # Refresh definitions so docs stay current.
            paths[key] = value
            added += 1
    return added


def upgrade_webhook_events(spec: dict) -> None:
    schema = (spec.get("components") or {}).get("schemas", {}).get("WebhookEvent")
    if not isinstance(schema, dict):
        return
    batch_events = [
        "batch.created",
        "batch.pending",
        "batch.processing",
        "batch.partial",
        "batch.failed",
        "batch.error",
    ]
    enum = list(schema.get("enum") or [])
    for event in batch_events:
        if event not in enum:
            enum.append(event)
    schema["enum"] = enum
    x_enum = schema.setdefault("x-enumDescriptions", {})
    if isinstance(x_enum, dict):
        x_enum.update(
            {
                "batch.created": "Mixed/bulk session created.",
                "batch.pending": "Mixed/bulk session pending customer action.",
                "batch.processing": "Mixed/bulk session has at least one step in flight.",
                "batch.partial": "Mixed/bulk session finished with mixed step outcomes.",
                "batch.failed": "Mixed/bulk session failed.",
                "batch.error": "Mixed/bulk session errored.",
            }
        )
    desc = schema.get("description")
    if isinstance(desc, str) and "batch." not in desc:
        schema["description"] = (
            desc.rstrip()
            + "\n\nMixed verification sessions also emit `batch.*` lifecycle events "
            "(in addition to per-child `sf.`/`kr.` verification events)."
        )


def upgrade_info_description(spec: dict) -> None:
    info = spec.get("info")
    if not isinstance(info, dict) or not isinstance(info.get("description"), str):
        return
    desc = info["description"]
    mixed_block = (
        "\n\nMixed verification (templates + hosted multi-step sessions):\n\n"
        "- `GET /api/v2/public/verifications/mixed-verifications/availability/`\n"
        "- `GET|POST /api/v2/public/verifications/mixed-verifications/templates/`\n"
        "- `GET|PATCH /api/v2/public/verifications/mixed-verifications/templates/{id}/`\n"
        "- `POST /api/v2/public/verifications/mixed-verifications/sessions/`\n"
        "- `GET /api/v2/public/verifications/mixed-verifications/sessions/{id}/`\n"
        "- `POST /api/v2/public/verifications/mixed-verifications/sessions/{id}/steps/{step_id}/`\n"
    )
    if "mixed-verifications/availability" not in desc:
        # Insert after product create list / before Retrieve line when present.
        marker = "Retrieve a verification via"
        if marker in desc:
            desc = desc.replace(marker, mixed_block.strip() + "\n\n" + marker, 1)
        else:
            desc = desc.rstrip() + mixed_block

    note = (
        "\n\nGovernment registry API reference operations are listed per "
        "`verification_type` for readability; the live create URL is always "
        "`POST /api/v2/public/verifications/requests/government_registry_checks/` "
        "with `verification_type` in the body.\n"
    )
    if "listed per" not in desc:
        desc = desc.rstrip() + note

    info["description"] = desc


def main() -> None:
    for path in (JSON_PATH, YAML_PATH):
        spec = json.loads(path.read_text())
        ensure_servers(spec)
        ensure_tags(spec)
        ttl_fixed = fix_ttl_enums(spec)
        fix_facial_screening(spec)
        mixed_added = ensure_mixed_paths(spec)
        upgrade_webhook_events(spec)
        upgrade_info_description(spec)
        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
        print(
            f"{path.name}: ttl_enums={ttl_fixed}, mixed_ops={mixed_added}, "
            f"servers={len(spec.get('servers', []))}"
        )


if __name__ == "__main__":
    main()
