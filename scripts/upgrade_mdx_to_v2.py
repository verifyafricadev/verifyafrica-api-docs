#!/usr/bin/env python3
"""Upgrade docs MDX pages from v1 X-API-KEY to v2 public Bearer API."""

from __future__ import annotations

import re
from pathlib import Path

PAGES = Path(__file__).resolve().parents[1] / "docs" / "pages"

ENDPOINT = "POST https://api.verifyafrica.io/api/v2/public/verifications/requests/"
DETAIL = "GET https://api.verifyafrica.io/api/v2/public/verifications/requests/{verification_id}/detail/"

AUTH_LINE = (
    'Authenticate with `Authorization: Bearer <VA-…api-key>` and set `verification_type` to `{type}`.'
)

BULK_SECTION_RE = re.compile(
    r"\n## Bulk Processing\n.*?(?=\n## |\Z)",
    re.DOTALL,
)

TIP_BLOCK_RE = re.compile(
    r":::tip API Reference\n.*?:::\n*",
    re.DOTALL,
)

API_REF_SECTION_RE = re.compile(
    r"\n## API Reference\n.*?(?=\n## |\Z)",
    re.DOTALL,
)

MODES_SECTION_RE = re.compile(
    r"\n## Verification Modes\n.*?(?=\n## |\Z)",
    re.DOTALL,
)


def verification_type_from(content: str) -> str | None:
    match = re.search(r"## Verification Type\n+\n```\n([a-z0-9_]+)\n```", content)
    return match.group(1) if match else None


def new_tip_and_api_ref(vtype: str | None, title_slug: str) -> tuple[str, str]:
    # Keep category anchors loosely; single create is the only create path now.
    tip = (
        ":::tip API Reference\n"
        "Jump directly to the interactive API docs:\n\n"
        "- [API reference](/api) — schemas, examples, and playground\n"
        "- Create: `POST /api/v2/public/verifications/requests/`\n"
        "- Detail: `GET /api/v2/public/verifications/requests/{verification_id}/detail/`\n"
        ":::\n\n"
    )
    api_ref = (
        "\n## API Reference\n\n"
        "View the full request/response schemas, response codes, and interactive playground:\n\n"
        "- [API reference](/api)\n"
    )
    return tip, api_ref


def transform_endpoint_page(content: str) -> str:
    vtype = verification_type_from(content)
    tip, api_ref = new_tip_and_api_ref(vtype, "")

    content = TIP_BLOCK_RE.sub(tip, content, count=1)
    content = MODES_SECTION_RE.sub("\n", content)
    content = BULK_SECTION_RE.sub("\n", content)
    content = API_REF_SECTION_RE.sub(api_ref, content)

    content = content.replace(
        "POST https://api.verifyafrica.io/api/verifications/requests/",
        ENDPOINT,
    )
    content = re.sub(
        r"Include your API key in the `X-API-KEY` header and set `verification_type` to `([^`]+)`\.",
        lambda m: AUTH_LINE.format(type=m.group(1)),
        content,
    )

    # Remove is_test and method_type from sample JSON blocks
    content = re.sub(r'\n\s*"is_test":\s*false,?\n?', "\n", content)
    content = re.sub(r'\n\s*"method_type":\s*"[^"]+",?\n?', "\n", content)

    # Clean trailing commas before closing braces that may result
    content = re.sub(r",(\s*})", r"\1", content)

    # Soften hosted-link language in use cases / param descriptions for identity pages
    content = content.replace(
        "Offer hosted verification links for end-user capture",
        "Validate government-issued IDs with direct document proofs",
    )
    content = content.replace(
        "Customer's email address. Used to send the hosted verification link.",
        "Customer's email address.",
    )
    content = content.replace(
        "Language for the hosted verification page (e.g., \"EN\", \"FR\"). Defaults to \"EN\".",
        'Language code (e.g., "EN", "FR"). Defaults to "EN".',
    )
    content = content.replace(
        "Link expiry time in minutes. Allowed: 30, 60, 180, 360, 720, 1440, 2880. Defaults to 60.",
        "Optional TTL in minutes when applicable. Allowed: 30, 60, 180, 360, 720, 1440, 2880. Defaults to 60.",
    )

    # Note offsite-only for create
    if "## Making a Request" in content and "direct (offsite)" not in content:
        content = content.replace(
            "## Making a Request\n",
            "## Making a Request\n\n"
            "Public API creates always use **direct (offsite)** mode. "
            "Do not send `method_type` — the API forces `offsite`.\n\n",
        )

    # Onsite-only products caution
    if vtype in {"crypto_wallet_screening", "risk_assessment"}:
        caution = (
            "\n:::caution Not available on public create\n"
            "This verification type currently requires a hosted (`onsite`) flow and is "
            "**not supported** by `POST /api/v2/public/verifications/requests/` "
            "(which always uses direct/offsite mode).\n"
            ":::\n"
        )
        if "Not available on public create" not in content:
            content = content.replace(
                f"```\n{vtype}\n```\n",
                f"```\n{vtype}\n```\n{caution}",
            )

    # id_document / face_match: document proof requirements for offsite
    if vtype == "id_document" and "`document.proof`" not in content:
        content = content.replace(
            "| `ttl` | number | No | Optional TTL in minutes when applicable. Allowed: 30, 60, 180, 360, 720, 1440, 2880. Defaults to 60. |\n",
            "| `ttl` | number | No | Optional TTL in minutes when applicable. Allowed: 30, 60, 180, 360, 720, 1440, 2880. Defaults to 60. |\n"
            "| `document` | object | Yes | Document payload. For direct mode, include `document.proof` (image URL or base64). |\n",
        )
    if vtype == "face_match" and "`face.proof`" not in content:
        content = content.replace(
            "| `ttl` | number | No | Optional TTL in minutes when applicable. Allowed: 30, 60, 180, 360, 720, 1440, 2880. Defaults to 60. |\n",
            "| `face` | object | Yes | Face payload. For direct mode, include `face.proof` and `face.verification_mode`. |\n",
        )

    return content


def transform_overview(content: str) -> str:
    content = content.replace(
        "POST https://api.verifyafrica.io/api/verifications/requests/",
        ENDPOINT,
    )
    content = re.sub(
        r"- \[Bulk API[^\]]*\]\([^\)]*\)\n?",
        "",
        content,
    )
    content = content.replace(
        "- [Single API — Identity Verification](/api/single-identity-verification)\n",
        "- [API Reference](/api)\n",
    )
    content = content.replace(
        "- [Single API — Compliance & Screening](/api/single-compliance-screening)\n",
        "- [API Reference](/api)\n",
    )
    content = content.replace(
        "- [Single API — Address Verification](/api/single-address-verification)\n",
        "- [API Reference](/api)\n",
    )
    content = content.replace(
        "- [Single API — Risk & Crypto](/api/single-risk-crypto)\n",
        "- [API Reference](/api)\n",
    )
    content = re.sub(
        r"\(\[API\]\(/api/single-[^\)]+\)\)",
        "([API](/api))",
        content,
    )
    content = re.sub(
        r"\(\[API\]\(/api/bulk-[^\)]+\)\)",
        "",
        content,
    )
    if "Getting Started" in content and DETAIL not in content and ENDPOINT in content:
        content = content.replace(
            f"All endpoints in this category use the same base URL:\n\n`{ENDPOINT}`\n",
            "All endpoints in this category use the public v2 create endpoint:\n\n"
            f"`{ENDPOINT}`\n\n"
            f"Retrieve results with `{DETAIL}`.\n\n"
            "Authenticate with `Authorization: Bearer <VA-…api-key>`.\n",
        )
    return content


def transform_introduction(content: str) -> str:
    return """\
---
title: VerifyAfrica API
description: Get started with the VerifyAfrica identity verification API. Verify documents, screen for AML risk, validate addresses, and query official registries across Nigeria, Ghana, Kenya, South Africa, and more.
sidebar_label: Introduction
sidebar_icon: sparkles
---

# VerifyAfrica API

VerifyAfrica provides identity verification, compliance screening, and government registry checks across Africa. Use a single API to verify documents, screen for AML risk, validate addresses, and query official registries in Nigeria, Ghana, Kenya, South Africa, and more.

## Base URL

```
https://api.verifyafrica.io
```

## Authentication

Include your tenant API key as a Bearer token on every request:

```
Authorization: Bearer VA-your_api_key_here
```

Do not send `X-API-KEY`. The API key identifies the tenant — no `X-TENANT-ID` header is required.

## Core Endpoints

| Endpoint | Description |
| --- | --- |
| `POST /api/v2/public/verifications/requests/` | Create and run a single verification (direct/offsite) |
| `GET /api/v2/public/verifications/requests/{verification_id}/detail/` | Retrieve verification status and details |

Every create request includes a `verification_type` that selects which check to run, plus an `input_data` object with the fields required for that check. Public creates always use **direct (offsite)** mode.

## Response format

Success:

```json
{
  "success": true,
  "message": "Verification request created successfully.",
  "data": { }
}
```

Error:

```json
{
  "success": false,
  "message": "…",
  "errors": ["…"]
}
```

## Verification Categories

Explore the **Endpoints** section in the sidebar for detailed guides on each verification type:

- **Identity Verification** — Document and facial screening
- **Compliance & Screening** — AML, business AML, and KYB checks
- **Address Verification** — Physical address validation
- **Risk & Crypto** — Fraud risk scoring and crypto wallet screening
- **Government Registry Checks** — Official ID and registry lookups by country

## Quick Example

```bash
curl -X POST https://api.verifyafrica.io/api/v2/public/verifications/requests/ \\
  -H "Authorization: Bearer VA-your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "verification_type": "ng_bvn_verification",
    "input_data": {
      "bvn": "22222222222",
      "first_name": "John",
      "last_name": "Doe"
    }
  }'
```

## Next Steps

- Browse [endpoint guides](/endpoints/overview/identity-verification) to learn what each verification type does
- Open the [API Reference](/api) for full schemas, parameters, and response codes
"""


def main() -> None:
    intro = PAGES / "introduction.mdx"
    intro.write_text(transform_introduction(intro.read_text()))
    print(f"Updated {intro.relative_to(PAGES.parent.parent)}")

    for path in sorted((PAGES / "endpoints").rglob("*.mdx")):
        original = path.read_text()
        rel = str(path.relative_to(PAGES / "endpoints"))
        if rel.startswith("overview/") or "/overview/" in rel:
            updated = transform_overview(original)
        else:
            updated = transform_endpoint_page(original)
        if updated != original:
            path.write_text(updated)
            print(f"Updated {path.relative_to(PAGES.parent.parent)}")


if __name__ == "__main__":
    main()
