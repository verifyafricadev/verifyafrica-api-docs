#!/usr/bin/env python3
"""Upgrade government registry OpenAPI ops to full link/direct parity with address/document."""

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "config" / "routes.oas.json"
YAML_PATH = ROOT / "config" / "openapi.yaml"
PRODUCT_PATH = "/api/v2/public/verifications/requests/government_registry_checks/"

# Matches backend METHOD_SCHEMAS / PARAMETER_LABELS
CHECKS: dict[str, dict] = {
    "za_said_verification": {
        "summary": "South Africa ID Verification",
        "country": "ZA",
        "required": ["id_number"],
        "optional": ["first_name", "last_name"],
        "selfie": False,
        "sample": {"id_number": "8012185201077", "first_name": "John", "last_name": "Doe"},
        "field_desc": {
            "id_number": "South African ID number.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
        },
    },
    "ng_bvn_verification": {
        "summary": "Nigeria BVN Verification",
        "country": "NG",
        "required": ["bvn"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {
            "bvn": "22222222222",
            "first_name": "Bimbo",
            "last_name": "Olakunle",
            "date_of_birth": "1988-04-04",
        },
        "field_desc": {
            "bvn": "11-digit Bank Verification Number.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "ng_nin_verification": {
        "summary": "Nigeria NIN Verification",
        "country": "NG",
        "required": ["nin"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {
            "nin": "55555555555",
            "first_name": "Bimbo",
            "last_name": "Olakunle",
            "date_of_birth": "1988-04-04",
        },
        "field_desc": {
            "nin": "11-digit National Identification Number.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "ng_virtual_nin_verification": {
        "summary": "Nigeria Virtual NIN",
        "country": "NG",
        "required": ["virtual_nin"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {"virtual_nin": "KO111111111111IL"},
        "field_desc": {
            "virtual_nin": "16-character Virtual NIN.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "ng_advanced_phone_number_verification": {
        "summary": "Nigeria Phone Verification",
        "country": "NG",
        "required": ["phone_number"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {"phone_number": "08000000000"},
        "field_desc": {
            "phone_number": "Nigerian phone number.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "ng_phone_number_lookup": {
        "summary": "Nigeria Phone Lookup",
        "country": "NG",
        "required": ["phone_number"],
        "optional": [],
        "selfie": False,
        "sample": {"phone_number": "08000000000"},
        "field_desc": {"phone_number": "Nigerian phone number."},
    },
    "ng_cac_lookup": {
        "summary": "Nigeria CAC Lookup",
        "country": "NG",
        "required": ["cac_number"],
        "optional": ["registration_name"],
        "selfie": False,
        "sample": {"cac_number": "RC00000011"},
        "field_desc": {
            "cac_number": "CAC registration number (e.g. RC00000011).",
            "registration_name": "Optional registered business name.",
        },
    },
    "ng_passport_verification": {
        "summary": "Nigeria Passport Verification",
        "country": "NG",
        "required": ["passport_id", "last_name"],
        "optional": [],
        "selfie": False,
        "sample": {"passport_id": "A01234567", "last_name": "Olakunle"},
        "field_desc": {
            "passport_id": "Passport number.",
            "last_name": "Last name as on the passport.",
        },
    },
    "gh_passport_lookup": {
        "summary": "Ghana Passport Lookup",
        "country": "GH",
        "required": ["passport_number"],
        "optional": ["first_name", "last_name", "date_of_birth"],
        "selfie": False,
        "sample": {"passport_number": "G0000555"},
        "field_desc": {
            "passport_number": "Ghana passport number.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
        },
    },
    "gh_voter_card_lookup": {
        "summary": "Ghana Voter Card Lookup",
        "country": "GH",
        "required": ["voter_id"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {"voter_id": "9001330422"},
        "field_desc": {
            "voter_id": "Ghana voter ID.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "gh_ssnit_lookup": {
        "summary": "Ghana SSNIT Lookup",
        "country": "GH",
        "required": ["ssnit_number"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {"ssnit_number": "C987464748977"},
        "field_desc": {
            "ssnit_number": "Ghana SSNIT number.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "gh_drivers_license_lookup": {
        "summary": "Ghana Drivers License Lookup",
        "country": "GH",
        "required": ["license_number"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {"license_number": "070667"},
        "field_desc": {
            "license_number": "Ghana driver's licence number.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "ke_passport_lookup": {
        "summary": "Kenya Passport Lookup",
        "country": "KE",
        "required": ["passport_number"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {"passport_number": "A2011111"},
        "field_desc": {
            "passport_number": "Kenya passport number.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "ke_national_id_lookup": {
        "summary": "Kenya National ID Lookup",
        "country": "KE",
        "required": ["national_id"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {"national_id": "25219766"},
        "field_desc": {
            "national_id": "Kenya national ID number.",
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "ke_phone_number_lookup": {
        "summary": "Kenya Phone Lookup",
        "country": "KE",
        "required": ["phone_number", "type"],
        "optional": [],
        "selfie": False,
        "sample": {"phone_number": "0723818211", "type": "national_id"},
        "field_desc": {
            "phone_number": "Kenya phone number.",
            "type": "Identity type linked to the phone — `national_id` or `passport`.",
        },
    },
    "ke_tax_pin_verification": {
        "summary": "Kenya Tax PIN Verification",
        "country": "KE",
        "required": ["tax_pin"],
        "optional": [],
        "selfie": False,
        "sample": {"tax_pin": "A009274635J"},
        "field_desc": {"tax_pin": "Kenya tax PIN."},
    },
    "ci_national_id_lookup": {
        "summary": "Côte d'Ivoire National ID Lookup",
        "country": "CI",
        "required": ["national_id"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {"national_id": "00112233440"},
        "field_desc": {
            "national_id": (
                "Ivorian National ID. 7–12 alphanumeric characters; "
                "normalized to uppercase before sending to Korapay."
            ),
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
    "ci_residence_card_lookup": {
        "summary": "Côte d'Ivoire Residence Card Lookup",
        "country": "CI",
        "required": ["residence_card_id"],
        "optional": ["first_name", "last_name", "date_of_birth", "selfie"],
        "selfie": True,
        "sample": {"residence_card_id": "11223344555"},
        "field_desc": {
            "residence_card_id": (
                "Ivorian Residence Card ID. 7–12 alphanumeric characters; "
                "normalized to uppercase before sending to Korapay."
            ),
            "first_name": "Optional first name for cross-validation.",
            "last_name": "Optional last name for cross-validation.",
            "date_of_birth": "Optional date of birth (YYYY-MM-DD).",
            "selfie": "Direct mode only. HTTPS URL of a selfie image for facial matching.",
        },
    },
}


def prop(desc: str, **extra) -> dict:
    out = {"type": "string", "description": desc}
    out.update(extra)
    return out


def build_description(vtype: str, meta: dict) -> str:
    req = ", ".join(f"`{k}`" for k in meta["required"])
    opt = meta["optional"]
    opt_no_selfie = [k for k in opt if k != "selfie"]
    opt_txt = ", ".join(f"`{k}`" for k in opt_no_selfie) or "none"
    selfie = meta["selfie"]
    lines = [
        f"Create a **{meta['summary']}** check in **link** or **direct** mode.",
        "",
        f"Call `POST {PRODUCT_PATH}` and set `verification_type` to `{vtype}`.",
        "",
        "### Link mode (`mode=link`, default)",
        f"**Required:** `input_data`, `input_data.email`",
        f"**Optional:** primary fields ({req}), validation fields ({opt_txt}), "
        "`send_email`, `input_data.ttl`"
        + (", `allow_file_upload`, `input_data.require_selfie`" if selfie else ""),
        "**Do not send:** `input_data.selfie` (proof URL)",
        "**Returns:** `data.link.url` for the hosted VerifyAfrica page",
        "Prefill any registry / validation field to lock it for the customer; omit fields so the customer enters them.",
        "",
        "### Direct mode (`mode=direct`)",
        f"**Required:** `input_data`, {req}",
        f"**Optional:** {opt_txt}"
        + (", `input_data.selfie` (HTTPS URL)" if selfie else ""),
        "**Do not send:** `send_email`, `allow_file_upload`, `input_data.ttl`, `input_data.require_selfie`",
        "**Returns:** accepted request (`PENDING`); Korapay Identity runs asynchronously",
        "",
        "Billing is deferred until the check is submitted to Korapay (not at HTTP create).",
        "Do not send internal `method_type`. Listen for `kr.verification.completed` / "
        "`kr.verification.failed` (or poll GET) for the terminal result.",
    ]
    return "\n".join(lines)


def build_input_properties(meta: dict) -> dict:
    props: dict = {
        "email": prop(
            "Link mode: required. Direct mode: optional customer email.",
            format="email",
        ),
        "language": prop('Both modes. Language code. Defaults to "EN".', example="EN", default="EN"),
        "ttl": {
            "type": "integer",
            "enum": [15, 30, 60, 120, 240],
            "default": 60,
            "description": "Link mode only. Hosted link lifetime in minutes. Defaults to 60. Omit in direct mode.",
        },
    }
    if meta["selfie"]:
        props["require_selfie"] = {
            "type": "boolean",
            "default": False,
            "description": "Link mode only. When true, the customer must capture or upload a selfie on the hosted page.",
        }
        props["allow_file_upload"] = {
            "type": "boolean",
            "description": "Link mode only. Same override as top-level `allow_file_upload`.",
        }
        props["selfie"] = prop(
            "Direct mode only. HTTPS URL of a selfie image. Base64 data URIs are rejected.",
            format="uri",
        )

    for key in [*meta["required"], *meta["optional"]]:
        if key == "selfie":
            continue
        if key == "type":
            props["type"] = {
                "type": "string",
                "enum": ["national_id", "passport"],
                "description": meta["field_desc"].get(key, key),
            }
            continue
        if key == "date_of_birth":
            props[key] = prop(
                meta["field_desc"].get(key, "Date of birth (YYYY-MM-DD)."),
                format="date",
                example="1988-04-04",
            )
            continue
        props[key] = prop(meta["field_desc"].get(key, key))
    return props


def build_request_schema(vtype: str, meta: dict) -> dict:
    properties: dict = {
        "mode": {
            "type": "string",
            "enum": ["link", "direct"],
            "default": "link",
            "description": "Both modes (defaults to `link`). `link` returns a hosted URL; `direct` runs Korapay Identity asynchronously.",
        },
        "verification_type": {
            "type": "string",
            "description": "Must match this check.",
            "enum": [vtype],
        },
        "send_email": {
            "type": "boolean",
            "default": False,
            "description": "Link mode only. `true` to email the hosted capture link to `input_data.email`. Defaults to `false`.",
        },
        "input_data": {
            "type": "object",
            "description": (
                f"Fields for `{vtype}`. In **direct** mode the primary identifier(s) are required. "
                "In **link** mode they are optional prefills (locked when sent)."
            ),
            "properties": build_input_properties(meta),
            "additionalProperties": False,
        },
    }
    if meta["selfie"]:
        properties["allow_file_upload"] = {
            "type": "boolean",
            "description": "Link mode only. Overrides the tenant product setting. `true` = camera + file upload; `false` = camera only.",
        }
    return {
        "type": "object",
        "required": ["verification_type", "input_data"],
        "properties": properties,
    }


def build_examples(vtype: str, meta: dict) -> dict:
    sample = meta["sample"]
    link_input = {
        "email": "customer@example.com",
        "language": "EN",
        "ttl": 60,
        **{k: v for k, v in sample.items() if k != "selfie"},
    }
    if meta["selfie"]:
        link_input["require_selfie"] = True

    link_body: dict = {
        "verification_type": vtype,
        "mode": "link",
        "send_email": True,
        "input_data": link_input,
    }
    if meta["selfie"]:
        link_body["allow_file_upload"] = True

    direct_input = {
        "language": "EN",
        **sample,
    }
    if meta["selfie"]:
        direct_input["selfie"] = "https://cdn.example.com/selfie.jpg"

    direct_body = {
        "verification_type": vtype,
        "mode": "direct",
        "input_data": direct_input,
    }

    return {
        "link": {
            "summary": "Link mode — hosted page",
            "value": link_body,
        },
        "direct": {
            "summary": "Direct mode — async Korapay Identity",
            "value": direct_body,
        },
        "default": {
            "summary": "Link mode — hosted page",
            "value": link_body,
        },
    }


def build_success_examples(vtype: str) -> dict:
    return {
        "link": {
            "summary": "Link mode — hosted URL returned",
            "value": {
                "success": True,
                "message": "Verification link created successfully.",
                "data": {
                    "id": "06ab25b4-0004-7048-8000-eba5ee027bbb",
                    "verification_type": vtype,
                    "status": "PENDING",
                    "created_at": "2026-09-22T10:41:04.035443Z",
                    "link": {
                        "url": "https://verify.verifyafrica.io/new-verify/25b6057a-7e63-4469-ad9f-45b3242e1d93"
                    },
                    "response_data": {},
                    "proofs": {},
                    "proofs_available": False,
                },
            },
        },
        "direct": {
            "summary": "Direct mode — accepted PENDING",
            "value": {
                "success": True,
                "message": (
                    "Verification request accepted. Processing has started; listen for the "
                    "kr.verification.completed webhook or poll GET "
                    "/api/v2/public/verifications/requests/?verification_id=…"
                ),
                "data": {
                    "id": "06ab25b4-0004-7048-8000-eba5ee027bbb",
                    "verification_type": vtype,
                    "status": "PENDING",
                    "created_at": "2026-09-22T10:41:04.035443Z",
                    "response_data": {},
                    "proofs": {},
                    "proofs_available": False,
                },
            },
        },
        "success": {
            "summary": "Direct mode — accepted PENDING",
            "value": {
                "success": True,
                "message": (
                    "Verification request accepted. Processing has started; listen for the "
                    "kr.verification.completed webhook or poll GET "
                    "/api/v2/public/verifications/requests/?verification_id=…"
                ),
                "data": {
                    "id": "06ab25b4-0004-7048-8000-eba5ee027bbb",
                    "verification_type": vtype,
                    "status": "PENDING",
                    "created_at": "2026-09-22T10:41:04.035443Z",
                    "response_data": {},
                    "proofs": {},
                    "proofs_available": False,
                },
            },
        },
    }


def upgrade_operation(op: dict, vtype: str, meta: dict) -> dict:
    op = copy.deepcopy(op)
    op["summary"] = meta["summary"]
    op["description"] = build_description(vtype, meta)
    content = op["requestBody"]["content"]["application/json"]
    content["schema"] = build_request_schema(vtype, meta)
    content["examples"] = build_examples(vtype, meta)
    content.pop("example", None)

    # Fix error example to use this vtype's primary field
    primary = meta["required"][0]
    err = (
        op.get("responses", {})
        .get("400", {})
        .get("content", {})
        .get("application/json", {})
        .get("examples", {})
        .get("error", {})
        .get("value")
    )
    if isinstance(err, dict):
        msg = f"Missing required parameters for '{vtype}': {primary}"
        err["message"] = msg
        err["errors"] = [msg]

    success_content = (
        op.get("responses", {})
        .get("201", {})
        .get("content", {})
        .get("application/json", {})
    )
    if success_content:
        success_content["examples"] = build_success_examples(vtype)
    return op


def upgrade_info_description(desc: str) -> str:
    old = (
        "Crypto, risk, and government registry creates behave like direct mode."
    )
    new = (
        "Crypto and risk creates behave like direct mode. "
        "**Government registry** checks support `mode=link` (hosted page; returns `data.link.url`) "
        "or `mode=direct` (async Korapay Identity). Billing is deferred until provider submit. "
        "Terminal webhooks use the `kr.` prefix (`kr.verification.completed` / `kr.verification.failed`)."
    )
    if old in desc:
        return desc.replace(old, new)
    if "Government registry** checks support" in desc or "government registry** checks support" in desc:
        return desc
    # Fallback: insert after KYB sentence if present
    needle = "Coverage: `GET /api/v2/public/verifications/supported-countries/?verification_type=kyb_screening&kyb_base=search`."
    if needle in desc and "Government registry" not in desc.split(needle, 1)[1][:200]:
        return desc.replace(
            needle,
            needle
            + " **Government registry** checks also support `mode=link` / `mode=direct` "
            "(Korapay Identity; `kr.` webhooks).",
        )
    return desc


GOV_WEBHOOK_COMPLETED = {
    "status": "success",
    "event": "kr.verification.completed",
    "data": {
        "id": "06ab25b4-0004-7048-8000-eba5ee027bbb",
        "verification_type": "ng_nin_verification",
        "status": "SUCCESS",
        "input_data": {
            "email": "customer@example.com",
            "language": "EN",
            "nin": "55555555555",
            "first_name": "Bimbo",
            "last_name": "Olakunle",
            "date_of_birth": "1988-04-04",
            "require_selfie": True,
        },
        "response_data": {
            "event": "kr.verification.completed",
            "verification_status": "verified",
        },
        "cost_charged": "0.50",
        "currency": "USD",
        "created_at": "2026-09-22T10:41:04.035443Z",
        "reference": "VER-019abc...",
        "by_api": True,
        "proofs": {},
        "proofs_available": False,
    },
}

GOV_WEBHOOK_FAILED = {
    "status": "failure",
    "event": "kr.verification.failed",
    "data": {
        "id": "06ab25b4-0004-7048-8000-eba5ee027bbb",
        "verification_type": "ng_nin_verification",
        "status": "FAILED",
        "input_data": {
            "nin": "55555555555",
        },
        "response_data": {
            "event": "kr.verification.failed",
            "verification_status": "invalid",
            "message": "Identity data not found.",
        },
        "cost_charged": "0.50",
        "currency": "USD",
        "created_at": "2026-09-22T10:41:04.035443Z",
        "reference": "VER-019abc...",
        "by_api": True,
        "proofs": {},
        "proofs_available": False,
    },
}


def upgrade_webhooks(spec: dict) -> None:
    schemas = spec.setdefault("components", {}).setdefault("schemas", {})
    payload = schemas.get("WebhookPayload")
    if isinstance(payload, dict):
        payload["description"] = (
            "JSON body POSTed to your configured webhook URL.\n\n"
            "Source of truth for webhook `event` names and payload shape.\n\n"
            "- `event: sf.verification.completed` / `kr.verification.completed` with `status: success` when the check passed\n"
            "- `event: sf.verification.failed` / `kr.verification.failed` with `status: failure` when the check did not succeed\n\n"
            "Government registry checks use the **`kr.`** prefix (Korapay Identity)."
        )
        status_prop = payload.get("properties", {}).get("status")
        if isinstance(status_prop, dict):
            status_prop["description"] = (
                "Envelope status aligned with the event: `success` for `*.verification.completed`, "
                "`failure` for `*.verification.failed`."
            )
        # Prefer a concrete prefixed example on the schema
        payload["example"] = {
            "status": "success",
            "event": "sf.verification.completed",
            "data": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "verification_type": "aml_screening",
                "status": "SUCCESS",
                "input_data": {},
                "response_data": {},
                "cost_charged": "1.00",
                "currency": "USD",
                "created_at": "2026-07-16T14:30:00.000Z",
                "batch_id": None,
                "reference": "VER-019abc...",
                "link": None,
                "email_sent_at": None,
                "by_api": True,
                "api_key_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
            },
        }

    webhooks = spec.get("webhooks") or {}
    completed = webhooks.get("verification.completed", {}).get("post")
    if isinstance(completed, dict):
        completed["summary"] = "sf./kr.verification.completed"
        completed["description"] = (
            "VerifyAfrica POSTs this event to your dashboard-configured webhook URL when a "
            "verification finishes successfully (`data.status` = `SUCCESS`).\n\n"
            "The `event` field is provider-prefixed: `sf.verification.completed` (Shufti) or "
            "`kr.verification.completed` (Korapay Identity / government registry).\n\n"
            "For unsuccessful outcomes, see `verification.failed`.\n\n"
            "Public API creates return `PENDING` immediately — use these webhooks (or poll GET) "
            "for the final result.\n\n"
            "**Auth:** when webhook auth is enabled, requests include `Authorization: Bearer <webhook_token>`.\n\n"
            "**Your endpoint must return HTTP 200.** Non-200 responses are retried up to 3 times (30s delay)."
        )
        examples = (
            completed.get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .setdefault("examples", {})
        )
        # Fix unprefixed default example
        default = examples.get("default", {})
        if isinstance(default.get("value"), dict):
            default["value"]["event"] = "sf.verification.completed"
            default["summary"] = "Shufti — document / AML / address"
        examples["government_registry"] = {
            "summary": "Korapay — government registry (NIN)",
            "value": GOV_WEBHOOK_COMPLETED,
        }

    failed = webhooks.get("verification.failed", {}).get("post")
    if isinstance(failed, dict):
        failed["summary"] = "sf./kr.verification.failed"
        failed["description"] = (
            "VerifyAfrica POSTs this event when a verification does not succeed "
            "(`data.status` = `FAILED` or `ERROR`).\n\n"
            "The `event` field is provider-prefixed: `sf.verification.failed` (Shufti) or "
            "`kr.verification.failed` (Korapay Identity / government registry).\n\n"
            "For successful outcomes, see `verification.completed`.\n\n"
            "**Auth:** when webhook auth is enabled, requests include `Authorization: Bearer <webhook_token>`.\n\n"
            "**Your endpoint must return HTTP 200.** Non-200 responses are retried up to 3 times (30s delay)."
        )
        examples = (
            failed.get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .setdefault("examples", {})
        )
        default = examples.get("default", {})
        if isinstance(default.get("value"), dict):
            default["value"]["event"] = "sf.verification.failed"
            default["summary"] = "Shufti — document / AML / address"
        examples["government_registry"] = {
            "summary": "Korapay — government registry (NIN)",
            "value": GOV_WEBHOOK_FAILED,
        }


def ensure_country_tags(spec: dict) -> None:
    tags = spec.setdefault("tags", [])
    by_name = {t.get("name"): t for t in tags if isinstance(t, dict)}
    desired = {
        "single-gov-south-africa": "South Africa",
        "single-gov-nigeria": "Nigeria",
        "single-gov-ghana": "Ghana",
        "single-gov-kenya": "Kenya",
        "single-gov-cote-divoire": "Côte d'Ivoire",
    }
    for name, display in desired.items():
        desc = (
            f"Government registry checks for {display}. Each operation supports "
            "`mode=link` (hosted) and `mode=direct` (async Korapay Identity)."
        )
        if name in by_name:
            by_name[name]["description"] = desc
            by_name[name]["x-displayName"] = display
        else:
            tags.append({"name": name, "description": desc, "x-displayName": display})

    groups = spec.get("x-tagGroups") or []
    for group in groups:
        if group.get("name") == "Government Registry Checks":
            group["tags"] = [
                "single-gov-south-africa",
                "single-gov-nigeria",
                "single-gov-ghana",
                "single-gov-kenya",
                "single-gov-cote-divoire",
            ]


COUNTRY_TAG_BY_CODE = {
    "ZA": "single-gov-south-africa",
    "NG": "single-gov-nigeria",
    "GH": "single-gov-ghana",
    "KE": "single-gov-kenya",
    "CI": "single-gov-cote-divoire",
}


def ensure_check_path(paths: dict, vtype: str, meta: dict, template_post: dict) -> None:
    key = f"{PRODUCT_PATH.rstrip('/')}/{vtype}"
    if key in paths and "post" in paths[key]:
        return
    op = copy.deepcopy(template_post)
    op["summary"] = meta["summary"]
    op["operationId"] = f"public-gov-{vtype}"
    op["tags"] = [COUNTRY_TAG_BY_CODE[meta["country"]]]
    paths[key] = {"post": op}


def ensure_public_verification_type_enum(spec: dict) -> None:
    schema = (spec.get("components") or {}).get("schemas", {}).get("PublicVerificationType")
    if not isinstance(schema, dict):
        return
    enum = list(schema.get("enum") or [])
    for vtype in CHECKS:
        if vtype not in enum:
            # Insert CI types after Kenya tax PIN when present
            if "ke_tax_pin_verification" in enum:
                idx = enum.index("ke_tax_pin_verification") + 1
                enum[idx:idx] = [v for v in (vtype,) if v not in enum]
            else:
                enum.append(vtype)
    # De-dupe while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for item in enum:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    schema["enum"] = ordered
    x_enum = schema.get("x-enumDescriptions")
    if isinstance(x_enum, dict):
        x_enum["ci_national_id_lookup"] = (
            "Côte d'Ivoire national ID (`POST .../government_registry_checks/`)"
        )
        x_enum["ci_residence_card_lookup"] = (
            "Côte d'Ivoire residence card (`POST .../government_registry_checks/`)"
        )


def main() -> None:
    for path in (JSON_PATH, YAML_PATH):
        spec = json.loads(path.read_text())
        paths = spec["paths"]
        ensure_country_tags(spec)
        ensure_public_verification_type_enum(spec)

        template_key = f"{PRODUCT_PATH.rstrip('/')}/ke_national_id_lookup"
        template_post = paths[template_key]["post"]

        updated = 0
        for vtype, meta in CHECKS.items():
            ensure_check_path(paths, vtype, meta, template_post)
            key = f"{PRODUCT_PATH.rstrip('/')}/{vtype}"
            node = paths.get(key)
            if not node or "post" not in node:
                print(f"MISSING {key}")
                continue
            node["post"] = upgrade_operation(node["post"], vtype, meta)
            node["post"]["tags"] = [COUNTRY_TAG_BY_CODE[meta["country"]]]
            updated += 1

        info = spec.get("info", {})
        if isinstance(info.get("description"), str):
            info["description"] = upgrade_info_description(info["description"])

        upgrade_webhooks(spec)

        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
        print(f"{path.name}: upgraded {updated} government registry operations")


if __name__ == "__main__":
    main()
