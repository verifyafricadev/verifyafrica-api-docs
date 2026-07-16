#!/usr/bin/env python3
"""Rewrite docs OpenAPI + MDX to product-scoped public create endpoints."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "config" / "routes.oas.json"
YAML_PATH = ROOT / "config" / "openapi.yaml"
PAGES = ROOT / "docs" / "pages"

BASE = "https://api.verifyafrica.io"
REQUESTS = "/api/v2/public/verifications/requests"
DETAIL = f"{REQUESTS}/?verification_id={{verification_id}}"

# verification_type path suffix → product slug
TYPE_TO_PRODUCT: dict[str, str] = {
    "id_document": "document_verification",
    "face_match": "facial_screening",
    "address_verification": "address_verification",
    "aml_screening": "aml_screening",
    "business_aml_screening": "business_aml_screening",
    "kyb_screening": "kyb",
    "crypto_wallet_screening": "crypto_wallet_screening",
    "risk_assessment": "risk_assessment",
}

GOV_TYPES = [
    "za_said_verification",
    "ng_bvn_verification",
    "ng_nin_verification",
    "ng_virtual_nin_verification",
    "ng_advanced_phone_number_verification",
    "ng_phone_number_lookup",
    "ng_cac_lookup",
    "ng_passport_verification",
    "gh_passport_lookup",
    "gh_voter_card_lookup",
    "gh_ssnit_lookup",
    "gh_drivers_license_lookup",
    "ke_passport_lookup",
    "ke_national_id_lookup",
    "ke_phone_number_lookup",
    "ke_tax_pin_verification",
]

# MDX file stem → product slug
MDX_TO_PRODUCT: dict[str, str] = {
    "id-document": "document_verification",
    "face-match": "facial_screening",
    "address-verification": "address_verification",
    "aml-screening": "aml_screening",
    "business-aml-screening": "business_aml_screening",
    "kyb-screening": "kyb",
    "crypto-wallet-screening": "crypto_wallet_screening",
    "risk-assessment": "risk_assessment",
    "za-said-verification": "government_registry_checks",
    "ng-bvn-verification": "government_registry_checks",
    "ng-nin-verification": "government_registry_checks",
    "ng-virtual-nin-verification": "government_registry_checks",
    "ng-advanced-phone-number-verification": "government_registry_checks",
    "ng-phone-number-lookup": "government_registry_checks",
    "ng-cac-lookup": "government_registry_checks",
    "ng-passport-verification": "government_registry_checks",
    "gh-passport-lookup": "government_registry_checks",
    "gh-voter-card-lookup": "government_registry_checks",
    "gh-ssnit-lookup": "government_registry_checks",
    "gh-drivers-license-lookup": "government_registry_checks",
    "ke-passport-lookup": "government_registry_checks",
    "ke-national-id-lookup": "government_registry_checks",
    "ke-phone-number-lookup": "government_registry_checks",
    "ke-tax-pin-verification": "government_registry_checks",
}

UNSUPPORTED: set[str] = set()

INFO_DESCRIPTION = """\
Identity verification, compliance screening, and government registry checks across Africa.

## Authentication

All endpoints require a tenant API key as a Bearer token:

```
Authorization: Bearer VA-your_api_key_here
```

Do not send `X-API-KEY`. Tenant context comes from the API key — no `X-TENANT-ID` header is required.

## API Sections

Create via product-scoped endpoints:

- `POST /api/v2/public/verifications/requests/document_verification/`
- `POST /api/v2/public/verifications/requests/facial_screening/`
- `POST /api/v2/public/verifications/requests/address_verification/`
- `POST /api/v2/public/verifications/requests/aml_screening/`
- `POST /api/v2/public/verifications/requests/business_aml_screening/`
- `POST /api/v2/public/verifications/requests/kyb/`
- `POST /api/v2/public/verifications/requests/crypto_wallet_screening/`
- `POST /api/v2/public/verifications/requests/risk_assessment/`
- `POST /api/v2/public/verifications/requests/government_registry_checks/`

Retrieve a verification via `GET /api/v2/public/verifications/requests/?verification_id={verification_id}`.

Public creates always run in **direct (offsite)** mode and return immediately with `status: PENDING`.
Hosted/link (`onsite`) flows are not available on this API.
Use webhooks (`verification.completed` / `verification.failed`) or GET for the final result.

## Public response shape

- Provider-agnostic: internal provider names and hosted provider URLs are never exposed
- Document/face proofs must be **HTTPS URLs** (base64 data URIs are rejected)
- `input_data.*.proof` and top-level `proofs` echo the original URLs from create time
- `response_data` is sanitized (no access tokens, provider proof links, or verification URLs)

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


def product_base_url(product: str) -> str:
    return f"{BASE}{REQUESTS}/{product}/"


def strip_verification_type_from_body(op: dict, *, keep_enum: list[str] | None = None) -> None:
    content = op.get("requestBody", {}).get("content", {}).get("application/json", {})
    schema = content.get("schema")
    if not isinstance(schema, dict):
        return
    props = schema.get("properties", {})
    required = schema.get("required")
    if keep_enum is None:
        props.pop("verification_type", None)
        if isinstance(required, list):
            schema["required"] = [r for r in required if r != "verification_type"]
        # examples
        examples = content.get("examples", {})
        if isinstance(examples, dict):
            for ex in examples.values():
                if isinstance(ex, dict) and isinstance(ex.get("value"), dict):
                    ex["value"].pop("verification_type", None)
        if isinstance(content.get("example"), dict):
            content["example"].pop("verification_type", None)
    else:
        props["verification_type"] = {
            "type": "string",
            "description": "Government registry verification type.",
            "enum": keep_enum,
        }
        if isinstance(required, list) and "verification_type" not in required:
            schema["required"] = ["verification_type", *[r for r in required if r != "verification_type"]]
        elif not required:
            schema["required"] = ["verification_type", "input_data"]


def set_zuplo_base(op: dict, product: str) -> None:
    route = op.setdefault("x-zuplo-route", {})
    handler = route.setdefault("handler", {})
    handler["export"] = "urlForwardHandler"
    handler["module"] = "$import(@zuplo/runtime)"
    options = handler.setdefault("options", {})
    options["baseUrl"] = product_base_url(product)


def transform_openapi(spec: dict) -> dict:
    spec = copy.deepcopy(spec)
    spec["info"]["description"] = INFO_DESCRIPTION
    old_paths = spec.get("paths", {})
    new_paths: dict = {}

    # Preserve / build GET detail on collection path
    detail_get = None
    for path, methods in old_paths.items():
        if path.endswith("/detail/") or path.rstrip("/").endswith("detail"):
            detail_get = methods.get("get")
        if path == f"{REQUESTS}/" and "get" in methods:
            detail_get = methods["get"]

    # Single-type products
    for vtype, product in TYPE_TO_PRODUCT.items():
        old_key = f"{REQUESTS}/{vtype}"
        methods = old_paths.get(old_key)
        if not methods or "post" not in methods:
            print(f"WARN missing source path {old_key}")
            continue
        op = copy.deepcopy(methods["post"])
        strip_verification_type_from_body(op, keep_enum=None)
        set_zuplo_base(op, product)
        op["operationId"] = f"public-{product}"
        new_paths[f"{REQUESTS}/{product}/"] = {"post": op}

    # Government — merge
    gov_ops = []
    gov_examples = {}
    for vtype in GOV_TYPES:
        old_key = f"{REQUESTS}/{vtype}"
        methods = old_paths.get(old_key)
        if not methods or "post" not in methods:
            continue
        op = copy.deepcopy(methods["post"])
        gov_ops.append(op)
        content = op.get("requestBody", {}).get("content", {}).get("application/json", {})
        examples = content.get("examples") or {}
        if examples:
            for name, ex in examples.items():
                gov_examples[f"{vtype}_{name}"] = ex
        elif content.get("example"):
            gov_examples[vtype] = {"summary": vtype, "value": content["example"]}
        else:
            # synthesize from schema example fields if present
            schema = content.get("schema", {})
            # try default example in tip style
            pass

    if gov_ops:
        base_op = copy.deepcopy(gov_ops[0])
        base_op["summary"] = "Government Registry Checks"
        base_op["description"] = (
            "Validate individuals and entities against government registries "
            "(South Africa, Nigeria, Ghana, Kenya).\n\n"
            "Include `verification_type` in the body to select the specific check "
            "(e.g. `ng_bvn_verification`). Public creates always use direct (offsite) mode."
        )
        base_op["operationId"] = "public-government_registry_checks"
        strip_verification_type_from_body(base_op, keep_enum=GOV_TYPES)
        content = base_op.get("requestBody", {}).get("content", {}).get("application/json", {})
        if gov_examples:
            content["examples"] = gov_examples
        # Flexible input_data — merge properties from all gov schemas when possible
        merged_props: dict = {}
        for op in gov_ops:
            schema = (
                op.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            input_schema = schema.get("properties", {}).get("input_data", {})
            for k, v in input_schema.get("properties", {}).items():
                merged_props.setdefault(k, v)
        input_data = content.get("schema", {}).get("properties", {}).get("input_data")
        if isinstance(input_data, dict) and merged_props:
            input_data["properties"] = merged_props
            input_data.pop("required", None)
            input_data["additionalProperties"] = True
        set_zuplo_base(base_op, "government_registry_checks")
        new_paths[f"{REQUESTS}/government_registry_checks/"] = {"post": base_op}

    # Detail GET — standalone section (not under Identity Verification)
    DETAIL_TAG = "public-verification-detail"
    if detail_get is None:
        detail_get = {
            "summary": "Get verification detail",
            "description": "Retrieve a verification request by ID.",
            "operationId": "public-verification-detail",
            "tags": [DETAIL_TAG],
            "security": [{"BearerAuth": []}],
            "parameters": [],
            "responses": {"200": {"description": "OK"}},
        }
    else:
        detail_get = copy.deepcopy(detail_get)

    detail_get["tags"] = [DETAIL_TAG]
    detail_get["parameters"] = [
        {
            "name": "verification_id",
            "in": "query",
            "required": True,
            "schema": {"type": "string", "format": "uuid"},
            "description": "Verification request ID returned from create.",
        }
    ]
    detail_get["operationId"] = "public-verification-detail"
    route = detail_get.setdefault("x-zuplo-route", {})
    handler = route.setdefault("handler", {})
    handler["export"] = "urlForwardHandler"
    handler["module"] = "$import(@zuplo/runtime)"
    handler.setdefault("options", {})["baseUrl"] = f"{BASE}{REQUESTS}/"

    new_paths[f"{REQUESTS}/"] = {"get": detail_get}
    spec["paths"] = new_paths

    tags = [t for t in spec.get("tags", []) if t.get("name") != DETAIL_TAG]
    tags.insert(
        0,
        {
            "name": DETAIL_TAG,
            "description": "Retrieve an existing verification request by ID.",
            "x-displayName": "Get verification detail",
        },
    )
    spec["tags"] = tags

    # Leave detail tag ungrouped so it is not triple-nested under a tag group.
    # zudoku.config.tsx navigationRules promote the GET op to a single root item.
    groups = []
    for group in spec.get("x-tagGroups") or []:
        cleaned = {
            **group,
            "tags": [t for t in group.get("tags", []) if t != DETAIL_TAG],
        }
        if cleaned["tags"] and cleaned.get("name") != "Get verification detail":
            groups.append(cleaned)
    spec["x-tagGroups"] = groups
    return spec


def verification_type_from_mdx(content: str) -> str | None:
    match = re.search(r"## Verification Type\n+\n```\n([a-z0-9_]+)\n```", content)
    return match.group(1) if match else None


def update_endpoint_mdx(path: Path) -> bool:
    stem = path.stem
    original = path.read_text()
    content = original

    if stem in UNSUPPORTED:
        # Point create URL at product path that does not exist — keep unsupported note
        content = re.sub(
            r"- Create: `POST [^`]+`",
            "- Create: not available on the public API (onsite-only)",
            content,
        )
        content = re.sub(
            r"- Detail: `GET [^`]+`",
            f"- Detail: `GET {DETAIL}`",
            content,
        )
        content = re.sub(
            r"\*\*Endpoint:\*\* `POST [^`]+`",
            "**Endpoint:** not available on the public API",
            content,
        )
        content = re.sub(
            r"not supported` by `POST [^`]+`",
            "not supported` by the public product create endpoints",
            content,
        )
        content = re.sub(
            r"not supported by `POST [^`]+`",
            "not supported by the public product create endpoints",
            content,
        )
        if content != original:
            path.write_text(content)
            return True
        return False

    product = MDX_TO_PRODUCT.get(stem)
    if not product:
        # overview pages handled separately
        return False

    create_path = f"{REQUESTS}/{product}/"
    create_full = f"POST {BASE}{create_path}"
    is_gov = product == "government_registry_checks"
    vtype = verification_type_from_mdx(content)

    tip = (
        ":::tip API Reference\n"
        "Jump directly to the interactive API docs:\n\n"
        "- [API reference](/api) — schemas, examples, and playground\n"
        f"- Create: `POST {create_path}`\n"
        f"- Detail: `GET {DETAIL}`\n"
        ":::"
    )
    content = re.sub(r":::tip API Reference\n.*?:::", tip, content, count=1, flags=re.DOTALL)

    content = re.sub(
        r"\*\*Endpoint:\*\* `POST [^`]+`",
        f"**Endpoint:** `{create_full}`",
        content,
    )

    if is_gov:
        auth = (
            f"Authenticate with `Authorization: Bearer <VA-…api-key>` "
            f"and set `verification_type` to `{vtype}`."
        )
        content = re.sub(
            r"Authenticate with `Authorization: Bearer <VA-…api-key>`[^\n]*",
            auth,
            content,
        )
        # Keep verification_type in JSON examples
    else:
        auth = "Authenticate with `Authorization: Bearer <VA-…api-key>`. The product path selects the verification type — do not send `verification_type`."
        content = re.sub(
            r"Authenticate with `Authorization: Bearer <VA-…api-key>`[^\n]*",
            auth,
            content,
        )
        # Remove verification_type from JSON example blocks under Making a Request
        def strip_vt_json(match: re.Match) -> str:
            block = match.group(0)
            block = re.sub(
                r'\n\s*"verification_type":\s*"[^"]+",?\n',
                "\n",
                block,
                count=1,
            )
            return block

        content = re.sub(
            r"## Making a Request\n.*?```json\n\{.*?\}\n```",
            strip_vt_json,
            content,
            count=1,
            flags=re.DOTALL,
        )
        # also strip allow_offline from examples if present
        content = re.sub(r'\n\s*"allow_offline":\s*(true|false),?\n', "\n", content)

    if content != original:
        path.write_text(content)
        return True
    return False


def update_overview_mdx(path: Path) -> bool:
    original = path.read_text()
    content = original
    # Replace generic create URL mentions with product-oriented wording
    replacements = [
        (
            f"`POST {BASE}{REQUESTS}/`",
            "product create endpoints under "
            f"`POST {BASE}{REQUESTS}/{{product}}/`",
        ),
        (
            f"GET {BASE}{REQUESTS}/{{verification_id}}/detail/",
            f"GET {BASE}{DETAIL}",
        ),
        (
            f"GET {REQUESTS}/{{verification_id}}/detail/",
            f"GET {DETAIL}",
        ),
        (
            f"`GET {BASE}{REQUESTS}/?verification_id={{verification_id}}`",
            f"`GET {BASE}{DETAIL}`",
        ),
    ]
    for old, new in replacements:
        content = content.replace(old, new)

    # More specific overview product URLs
    stem = path.stem
    parent = path.parent.name
    product_map = {
        "identity-verification": None,  # two products
        "compliance-screening": None,
        "address-verification": "address_verification",
        "risk-crypto": None,
    }

    if stem == "address-verification" and "overview" in str(path):
        content = re.sub(
            r"product create endpoints under `POST [^`]+`",
            f"`POST {BASE}{REQUESTS}/address_verification/`",
            content,
        )
        content = content.replace(
            f"`POST {BASE}{REQUESTS}/`",
            f"`POST {BASE}{REQUESTS}/address_verification/`",
        )

    if content != original:
        path.write_text(content)
        return True
    return False


def update_introduction() -> None:
    path = PAGES / "introduction.mdx"
    content = path.read_text()
    table = """\
## Core Endpoints

| Endpoint | Description |
| --- | --- |
| `POST /api/v2/public/verifications/requests/document_verification/` | Document verification |
| `POST /api/v2/public/verifications/requests/facial_screening/` | Facial screening |
| `POST /api/v2/public/verifications/requests/address_verification/` | Address verification |
| `POST /api/v2/public/verifications/requests/aml_screening/` | AML screening |
| `POST /api/v2/public/verifications/requests/business_aml_screening/` | Business AML screening |
| `POST /api/v2/public/verifications/requests/kyb/` | KYB (know your business) |
| `POST /api/v2/public/verifications/requests/crypto_wallet_screening/` | Crypto wallet screening |
| `POST /api/v2/public/verifications/requests/risk_assessment/` | Risk assessment |
| `POST /api/v2/public/verifications/requests/government_registry_checks/` | Government registry checks (include `verification_type` in body) |
| `GET /api/v2/public/verifications/requests/?verification_id={verification_id}` | Retrieve verification status and details |

Product paths lock the check for single-type products. For `government_registry_checks`, send `verification_type` in the body (e.g. `ng_bvn_verification`). Public creates always use **direct (offsite)** mode.
"""
    content = re.sub(
        r"## Core Endpoints\n.*?(?=\n## )",
        table + "\n",
        content,
        count=1,
        flags=re.DOTALL,
    )
    # Fix curl example if present
    content = re.sub(
        rf"{re.escape(BASE)}{re.escape(REQUESTS)}/",
        f"{BASE}{REQUESTS}/document_verification/",
        content,
        count=1,
    )
    # Avoid double-replacing product paths — only first generic curl
    path.write_text(content)
    print("updated introduction.mdx")


def update_overviews_carefully() -> None:
    mapping = {
        "identity-verification.mdx": (
            f"`POST {BASE}{REQUESTS}/document_verification/` and "
            f"`POST {BASE}{REQUESTS}/facial_screening/`"
        ),
        "compliance-screening.mdx": (
            f"`POST {BASE}{REQUESTS}/aml_screening/`, "
            f"`POST {BASE}{REQUESTS}/business_aml_screening/`, and "
            f"`POST {BASE}{REQUESTS}/kyb/`"
        ),
        "address-verification.mdx": f"`POST {BASE}{REQUESTS}/address_verification/`",
        "risk-crypto.mdx": (
            f"`POST {BASE}{REQUESTS}/risk_assessment/` and "
            f"`POST {BASE}{REQUESTS}/crypto_wallet_screening/`"
        ),
        "government-registry.mdx": f"`POST {BASE}{REQUESTS}/government_registry_checks/`",
    }
    for name, create_line in mapping.items():
        # search in overview dirs
        for path in PAGES.rglob(name):
            if "endpoints" not in str(path):
                continue
            original = path.read_text()
            content = original
            content = re.sub(
                rf"`?POST {re.escape(BASE)}{re.escape(REQUESTS)}/`?",
                create_line.strip("`"),
                content,
            )
            # Fix doubled backticks / awkward replacements
            content = re.sub(
                r"Retrieve results with `GET [^`]+`",
                f"Retrieve results with `GET {BASE}{DETAIL}`.",
                content,
            )
            content = re.sub(
                r"- Detail: `GET [^`]+`",
                f"- Detail: `GET {DETAIL}`",
                content,
            )
            if "risk-crypto" in name:
                content = re.sub(
                    r"(?m)^`POST .+$",
                    create_line if not create_line.startswith("`") else create_line,
                    content,
                    count=1,
                )
            if content != original:
                path.write_text(content)
                print(f"updated {path.relative_to(ROOT)}")


def main() -> None:
    for path in (JSON_PATH, YAML_PATH):
        spec = json.loads(path.read_text())
        updated = transform_openapi(spec)
        path.write_text(json.dumps(updated, indent=2) + "\n")
        print(f"updated {path.relative_to(ROOT)} paths={list(updated['paths'])}")

    changed = 0
    for path in (PAGES / "endpoints").glob("*.mdx"):
        if update_endpoint_mdx(path):
            changed += 1
            print(f"updated {path.relative_to(ROOT)}")
    print(f"endpoint mdx changed: {changed}")

    update_introduction()
    update_overviews_carefully()


if __name__ == "__main__":
    main()
