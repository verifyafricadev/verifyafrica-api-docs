#!/usr/bin/env python3
"""
Restructure OpenAPI government registry into:

  Government Registry Checks (tag group)
    → Country (tag)
      → Each check (operation)

All checks POST to the same product URL via x-zuplo-route baseUrl.
Also deep-links MDX tips to the matching API Reference anchors.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "config" / "routes.oas.json"
YAML_PATH = ROOT / "config" / "openapi.yaml"
PAGES = ROOT / "docs" / "pages" / "endpoints"

PRODUCT_URL = "https://api.verifyafrica.io/api/v2/public/verifications/requests/government_registry_checks/"
PRODUCT_PATH = "/api/v2/public/verifications/requests/government_registry_checks/"

# verification_type → (country_tag, summary, mdx_stem)
CHECKS: list[tuple[str, str, str, str]] = [
    ("za_said_verification", "single-gov-south-africa", "South Africa ID Verification", "za-said-verification"),
    ("ng_bvn_verification", "single-gov-nigeria", "Nigeria BVN Verification", "ng-bvn-verification"),
    ("ng_nin_verification", "single-gov-nigeria", "Nigeria NIN Verification", "ng-nin-verification"),
    ("ng_virtual_nin_verification", "single-gov-nigeria", "Nigeria Virtual NIN", "ng-virtual-nin-verification"),
    (
        "ng_advanced_phone_number_verification",
        "single-gov-nigeria",
        "Nigeria Phone Verification",
        "ng-advanced-phone-number-verification",
    ),
    ("ng_phone_number_lookup", "single-gov-nigeria", "Nigeria Phone Lookup", "ng-phone-number-lookup"),
    ("ng_cac_lookup", "single-gov-nigeria", "Nigeria CAC Lookup", "ng-cac-lookup"),
    ("ng_passport_verification", "single-gov-nigeria", "Nigeria Passport Verification", "ng-passport-verification"),
    ("gh_passport_lookup", "single-gov-ghana", "Ghana Passport Lookup", "gh-passport-lookup"),
    ("gh_voter_card_lookup", "single-gov-ghana", "Ghana Voter Card Lookup", "gh-voter-card-lookup"),
    ("gh_ssnit_lookup", "single-gov-ghana", "Ghana SSNIT Lookup", "gh-ssnit-lookup"),
    ("gh_drivers_license_lookup", "single-gov-ghana", "Ghana Drivers License Lookup", "gh-drivers-license-lookup"),
    ("ke_passport_lookup", "single-gov-kenya", "Kenya Passport Lookup", "ke-passport-lookup"),
    ("ke_national_id_lookup", "single-gov-kenya", "Kenya National ID Lookup", "ke-national-id-lookup"),
    ("ke_phone_number_lookup", "single-gov-kenya", "Kenya Phone Lookup", "ke-phone-number-lookup"),
    ("ke_tax_pin_verification", "single-gov-kenya", "Kenya Tax PIN Verification", "ke-tax-pin-verification"),
]

COUNTRY_TAGS = {
    "single-gov-south-africa": {
        "name": "single-gov-south-africa",
        "description": "Government registry checks for South Africa.",
        "x-displayName": "South Africa",
    },
    "single-gov-nigeria": {
        "name": "single-gov-nigeria",
        "description": "Government registry checks for Nigeria.",
        "x-displayName": "Nigeria",
    },
    "single-gov-ghana": {
        "name": "single-gov-ghana",
        "description": "Government registry checks for Ghana.",
        "x-displayName": "Ghana",
    },
    "single-gov-kenya": {
        "name": "single-gov-kenya",
        "description": "Government registry checks for Kenya.",
        "x-displayName": "Kenya",
    },
}

# Required input_data keys per verification_type (from MDX)
REQUIRED_INPUT: dict[str, list[str]] = {
    "za_said_verification": ["id_number"],
    "ng_bvn_verification": ["bvn"],
    "ng_nin_verification": ["nin"],
    "ng_virtual_nin_verification": ["vnin"],
    "ng_advanced_phone_number_verification": ["phone_number"],
    "ng_phone_number_lookup": ["phone_number"],
    "ng_cac_lookup": ["rc_number"],
    "ng_passport_verification": ["passport_number"],
    "gh_passport_lookup": ["passport_number"],
    "gh_voter_card_lookup": ["voter_id"],
    "gh_ssnit_lookup": ["ssnit_number"],
    "gh_drivers_license_lookup": ["license_number"],
    "ke_passport_lookup": ["passport_number"],
    "ke_national_id_lookup": ["id_number"],
    "ke_phone_number_lookup": ["phone_number"],
    "ke_tax_pin_verification": ["tax_pin"],
}


def slugify(summary: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", summary.lower()).strip("-")


def input_schema_from_example(example_value: dict, vtype: str) -> dict:
    input_data = example_value.get("input_data") or {}
    props = {key: {"type": "string"} for key in input_data}
    required = [k for k in REQUIRED_INPUT.get(vtype, []) if k in props] or list(props.keys())[:1]
    return {
        "type": "object",
        "description": f"Input fields for `{vtype}`.",
        "properties": props,
        "required": required,
        "additionalProperties": True,
    }


def build_check_operation(template: dict, vtype: str, tag: str, summary: str, example: dict | None) -> dict:
    op = copy.deepcopy(template)
    op["summary"] = summary
    op["operationId"] = f"public-gov-{vtype}"
    op["tags"] = [tag]
    op["description"] = (
        f"{summary}.\n\n"
        f"Call `POST {PRODUCT_PATH}` and set `verification_type` to `{vtype}`.\n\n"
        "Public creates always use direct (offsite) mode."
    )

    example_value = (example or {}).get("value") or {
        "verification_type": vtype,
        "input_data": {},
    }
    # Ensure verification_type is locked in example
    example_value = copy.deepcopy(example_value)
    example_value["verification_type"] = vtype

    content = op.setdefault("requestBody", {}).setdefault("content", {}).setdefault("application/json", {})
    content["schema"] = {
        "type": "object",
        "required": ["verification_type", "input_data"],
        "properties": {
            "verification_type": {
                "type": "string",
                "description": "Must match this check.",
                "enum": [vtype],
            },
            "input_data": input_schema_from_example(example_value, vtype),
        },
    }
    content["examples"] = {
        "default": {
            "summary": summary,
            "value": example_value,
        }
    }
    content.pop("example", None)

    route = op.setdefault("x-zuplo-route", {})
    handler = route.setdefault("handler", {})
    handler["export"] = "urlForwardHandler"
    handler["module"] = "$import(@zuplo/runtime)"
    handler.setdefault("options", {})["baseUrl"] = PRODUCT_URL
    return op


def transform(spec: dict) -> dict:
    spec = copy.deepcopy(spec)
    paths = spec.get("paths", {})

    merged = paths.pop(PRODUCT_PATH, None) or paths.pop(
        PRODUCT_PATH.rstrip("/"),
        None,
    )
    if not merged or "post" not in merged:
        raise SystemExit(f"Missing merged gov path {PRODUCT_PATH}")

    template = merged["post"]
    examples = (
        template.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("examples", {})
    )

    DETAIL_TAG = "public-verification-detail"

    # Drop empty country tags from leftover single-op merge; rebuild tags list
    other_tags = [
        t
        for t in spec.get("tags", [])
        if not str(t.get("name", "")).startswith("single-gov-")
        and t.get("name") != DETAIL_TAG
    ]
    detail_tag = {
        "name": DETAIL_TAG,
        "description": "Retrieve an existing verification request by ID.",
        "x-displayName": "Get verification detail",
    }
    spec["tags"] = [detail_tag, *other_tags, *COUNTRY_TAGS.values()]

    # Keep GET detail tagged standalone (not under Identity Verification)
    collection = paths.get("/api/v2/public/verifications/requests/")
    if collection and "get" in collection:
        collection["get"]["tags"] = [DETAIL_TAG]

    # Insert per-check paths (unique for OpenAPI; playground forwards to product URL)
    for vtype, tag, summary, _mdx in CHECKS:
        example = examples.get(f"{vtype}_default") or examples.get(vtype)
        op = build_check_operation(template, vtype, tag, summary, example)
        # Docs path includes check for uniqueness; real URL is PRODUCT_URL
        path_key = f"{PRODUCT_PATH.rstrip('/')}/{vtype}"
        paths[path_key] = {"post": op}

    spec["paths"] = paths

    # Tag groups: Detail (standalone) → Verifications → Government Registry Checks
    non_gov = [
        "single-identity-verification",
        "single-compliance-screening",
        "single-address-verification",
        "single-risk-crypto",
    ]
    existing = {t["name"] for t in spec["tags"]}
    non_gov = [t for t in non_gov if t in existing]

    # Detail tag is left ungrouped; zudoku.config navigationRules flatten it
    # to a single root sidebar item after Information.
    spec["x-tagGroups"] = [
        {"name": "Verifications", "tags": non_gov},
        {
            "name": "Government Registry Checks",
            "tags": [
                "single-gov-south-africa",
                "single-gov-nigeria",
                "single-gov-ghana",
                "single-gov-kenya",
            ],
        },
    ]
    return spec


def update_mdx_api_links() -> None:
    """Point MDX tip API links at country tag + check anchor."""
    for vtype, tag, summary, stem in CHECKS:
        path = PAGES / f"{stem}.mdx"
        if not path.exists():
            continue
        content = path.read_text()
        anchor = slugify(summary)
        api_link = f"/api/{tag}#{anchor}"
        # Replace generic /api tip link
        content = re.sub(
            r"- \[API reference\]\(/api[^)]*\)[^\n]*",
            f"- [API reference]({api_link}) — schemas, examples, and playground",
            content,
            count=1,
        )
        # Footer API Reference link if present
        content = re.sub(
            r"- \[API reference\]\(/api\)\s*$",
            f"- [API reference]({api_link})",
            content,
            flags=re.MULTILINE,
        )
        path.write_text(content)
        print(f"updated tip link {path.name} → {api_link}")


def update_country_overviews() -> None:
    overviews = {
        "south-africa.mdx": (
            "single-gov-south-africa",
            [("za-said-verification", "South Africa ID Verification")],
        ),
        "nigeria.mdx": (
            "single-gov-nigeria",
            [
                ("ng-bvn-verification", "Nigeria BVN Verification"),
                ("ng-nin-verification", "Nigeria NIN Verification"),
                ("ng-virtual-nin-verification", "Nigeria Virtual NIN"),
                ("ng-advanced-phone-number-verification", "Nigeria Phone Verification"),
                ("ng-phone-number-lookup", "Nigeria Phone Lookup"),
                ("ng-cac-lookup", "Nigeria CAC Lookup"),
                ("ng-passport-verification", "Nigeria Passport Verification"),
            ],
        ),
        "ghana.mdx": (
            "single-gov-ghana",
            [
                ("gh-passport-lookup", "Ghana Passport Lookup"),
                ("gh-voter-card-lookup", "Ghana Voter Card Lookup"),
                ("gh-ssnit-lookup", "Ghana SSNIT Lookup"),
                ("gh-drivers-license-lookup", "Ghana Drivers License Lookup"),
            ],
        ),
        "kenya.mdx": (
            "single-gov-kenya",
            [
                ("ke-passport-lookup", "Kenya Passport Lookup"),
                ("ke-national-id-lookup", "Kenya National ID Lookup"),
                ("ke-phone-number-lookup", "Kenya Phone Lookup"),
                ("ke-tax-pin-verification", "Kenya Tax PIN Verification"),
            ],
        ),
    }

    intro = (
        "All checks in this country use the same product endpoint:\n\n"
        f"`POST {PRODUCT_PATH}`\n\n"
        "Set `verification_type` to the identifier for the check you need. "
        "Retrieve results with "
        "`GET /api/v2/public/verifications/requests/?verification_id={verification_id}`.\n"
    )

    for filename, (tag, items) in overviews.items():
        path = PAGES / "overview" / "government-registry" / filename
        if not path.exists():
            continue
        content = path.read_text()
        # Replace API Reference section
        links = "\n".join(
            f"- [{label}](../../{stem}) — [API](/api/{tag}#{slugify(label)})"
            for stem, label in items
        )
        new_sections = (
            f"## API Reference\n\n"
            f"- [Country operations](/api/{tag})\n\n"
            f"{intro}\n"
            f"## Endpoints\n\n"
            f"{links}\n"
        )
        content = re.sub(
            r"## API Reference\n.*",
            new_sections.rstrip() + "\n",
            content,
            count=1,
            flags=re.DOTALL,
        )
        path.write_text(content)
        print(f"updated overview {filename}")

    # Top government-registry overview
    top = PAGES / "overview" / "government-registry.mdx"
    if top.exists():
        content = top.read_text()
        content = re.sub(
            r"## Getting Started\n.*",
            "## Getting Started\n\n"
            "Government registry checks use one product endpoint, organized by country in the "
            "[API Reference](/api):\n\n"
            f"`POST {PRODUCT_PATH}`\n\n"
            "Include `verification_type` in the body to select the specific check "
            "(for example `ng_bvn_verification`).\n\n"
            "Browse a country below, then open the check you need.\n",
            content,
            count=1,
            flags=re.DOTALL,
        )
        top.write_text(content)
        print("updated government-registry.mdx")


def main() -> None:
    for path in (JSON_PATH, YAML_PATH):
        spec = json.loads(path.read_text())
        updated = transform(spec)
        path.write_text(json.dumps(updated, indent=2) + "\n")
        gov_paths = [p for p in updated["paths"] if "government_registry_checks" in p]
        print(f"{path.name}: {len(gov_paths)} gov paths, tagGroups={updated['x-tagGroups']}")

    update_mdx_api_links()
    update_country_overviews()


if __name__ == "__main__":
    main()
