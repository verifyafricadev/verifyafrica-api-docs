#!/usr/bin/env python3
"""Run government registry public API tests (link + direct, success + fail).

Uses Korapay sandbox credentials from:
https://developers.korapay.com/docs/testing-your-integration

Writes one JSON file per scenario under docs/gov-registry-test-results/.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "gov-registry-test-results"

BASE_URL = os.environ.get("VA_PUBLIC_API_BASE", "http://localhost:8300").rstrip("/")
API_KEY = os.environ.get(
    "VA_PUBLIC_API_KEY",
    "VA-O6e_Ala-dqDeYTqAm57SKLLha0M49BX5MJQH6t2n3xzesRFVUOOXcip2SgJV0nLV",
)
CREATE_PATH = "/api/v2/public/verifications/requests/government_registry_checks/"
GET_PATH = "/api/v2/public/verifications/requests/"
SUBMIT_PATH = "/api/v2/verifications/new-verify/{token}/government_registry/"

POLL_INTERVAL_S = 1.5
POLL_TIMEOUT_S = 90

# Success / fail credentials from Korapay testing docs.
CHECKS: list[dict[str, Any]] = [
    {
        "verification_type": "za_said_verification",
        "success": {"id_number": "8012185201077"},
        "fail": {"id_number": "8000000000001"},
    },
    {
        "verification_type": "ng_bvn_verification",
        "success": {"bvn": "22222222222"},
        "fail": {"bvn": "00000000000"},
    },
    {
        "verification_type": "ng_nin_verification",
        "success": {"nin": "55555555555"},
        "fail": {"nin": "00000000000"},
    },
    {
        "verification_type": "ng_virtual_nin_verification",
        "success": {"virtual_nin": "KO111111111111IL"},
        "fail": {"virtual_nin": "KO000000000000II"},
    },
    {
        "verification_type": "ng_advanced_phone_number_verification",
        "success": {"phone_number": "08000000000"},
        "fail": {"phone_number": "08000000001"},
    },
    {
        "verification_type": "ng_phone_number_lookup",
        "success": {"phone_number": "08000000000"},
        "fail": {"phone_number": "08000000001"},
    },
    {
        "verification_type": "ng_cac_lookup",
        "success": {"cac_number": "RC00000011", "registration_type": "RC"},
        "fail": {"cac_number": "RC11111111", "registration_type": "RC"},
    },
    {
        "verification_type": "ng_passport_verification",
        "success": {"passport_id": "A01234567", "last_name": "Olakunle"},
        "fail": {"passport_id": "A00000000", "last_name": "Olakunle"},
    },
    {
        "verification_type": "gh_passport_lookup",
        "success": {"passport_number": "G0000555"},
        "fail": {"passport_number": "G0000000"},
    },
    {
        "verification_type": "gh_voter_card_lookup",
        "success": {"voter_id": "9001330422", "type": "old_voters_card"},
        "fail": {"voter_id": "0000000000", "type": "old_voters_card"},
    },
    {
        "verification_type": "gh_ssnit_lookup",
        "success": {"ssnit_number": "C987464748977"},
        "fail": {"ssnit_number": "C000000000000"},
    },
    {
        "verification_type": "gh_drivers_license_lookup",
        "success": {"license_number": "070667"},
        "fail": {"license_number": "000000"},
    },
    {
        "verification_type": "ke_passport_lookup",
        "success": {"passport_number": "A2011111"},
        "fail": {"passport_number": "A0000000"},
    },
    {
        "verification_type": "ke_national_id_lookup",
        "success": {"national_id": "25219766"},
        "fail": {"national_id": "00000000"},
    },
    {
        "verification_type": "ke_phone_number_lookup",
        "success": {"phone_number": "0723818211", "type": "national_id"},
        # No invalid phone listed in Korapay docs; use a clearly fake number.
        "fail": {"phone_number": "0700000000", "type": "national_id"},
        "fail_note": "Korapay docs list only a valid KE phone; fail uses a synthetic invalid number.",
    },
    {
        "verification_type": "ke_tax_pin_verification",
        "success": {"tax_pin": "A009274635J"},
        "fail": {"tax_pin": "A0000000000"},
    },
    {
        "verification_type": "ci_national_id_lookup",
        "success": {"national_id": "00112233440"},
        # Korapay CI docs list only a valid National ID; fail uses a synthetic invalid value.
        "fail": {"national_id": "00000000000"},
        "fail_note": "Korapay docs list only a valid CI National ID; fail uses a synthetic invalid ID.",
    },
    {
        "verification_type": "ci_residence_card_lookup",
        "success": {"residence_card_id": "11223344555"},
        "fail": {"residence_card_id": "00000000000"},
        "fail_note": "Korapay docs list only a valid CI Residence Card; fail uses a synthetic invalid ID.",
    },
]


def _request(method: str, path: str, body: dict | None = None, *, auth: bool = True) -> tuple[int, dict | list | str]:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if auth:
        headers["Authorization"] = f"Bearer {API_KEY}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            try:
                parsed: dict | list | str = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = raw
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else {"detail": str(exc)}
        except json.JSONDecodeError:
            parsed = {"detail": raw or str(exc)}
        return exc.code, parsed


def _truncate_large_strings(obj: Any, *, limit: int = 240) -> Any:
    """Keep JSON readable by truncating huge base64 image blobs."""
    if isinstance(obj, dict):
        return {k: _truncate_large_strings(v, limit=limit) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_truncate_large_strings(v, limit=limit) for v in obj]
    if isinstance(obj, str) and len(obj) > limit and (
        obj.startswith("/9j/") or obj.startswith("data:image") or re.fullmatch(r"[A-Za-z0-9+/=\s]{500,}", obj)
    ):
        return f"{obj[:80]}…<truncated {len(obj)} chars>"
    return obj


def _poll(verification_id: str) -> dict:
    deadline = time.time() + POLL_TIMEOUT_S
    last: dict = {}
    while time.time() < deadline:
        status, payload = _request("GET", f"{GET_PATH}?verification_id={verification_id}")
        if status != 200 or not isinstance(payload, dict):
            last = {"http_status": status, "body": payload}
            time.sleep(POLL_INTERVAL_S)
            continue
        last = payload
        data = payload.get("data") or {}
        if str(data.get("status") or "").upper() not in {"PENDING", "PROCESSING", "QUEUED", ""}:
            return payload
        time.sleep(POLL_INTERVAL_S)
    return last or {"error": "poll_timeout", "verification_id": verification_id}


def _token_from_link(create_response: dict) -> str | None:
    data = (create_response or {}).get("data") or {}
    link = data.get("link") or {}
    if link.get("link"):
        return str(link["link"])
    url = link.get("url") or ""
    path = urlparse(url).path.rstrip("/")
    if "/new-verify/" in path:
        return path.split("/new-verify/")[-1]
    return None


def _write_scenario(name: str, document: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(_truncate_large_strings(document), indent=2, ensure_ascii=False) + "\n")
    return path


def run_direct(check: dict, outcome: str) -> Path:
    vtype = check["verification_type"]
    fields = deepcopy(check[outcome])
    create_payload = {
        "verification_type": vtype,
        "mode": "direct",
        "input_data": fields,
    }
    create_status, create_body = _request("POST", CREATE_PATH, create_payload)
    verification_id = None
    if isinstance(create_body, dict):
        verification_id = ((create_body.get("data") or {}).get("id"))
    final = None
    if verification_id and create_status in {200, 201}:
        final = _poll(str(verification_id))
    doc = {
        "scenario": {
            "verification_type": vtype,
            "mode": "direct",
            "outcome": outcome,
            "source": "https://developers.korapay.com/docs/testing-your-integration",
            **({"note": check["fail_note"]} if outcome == "fail" and check.get("fail_note") else {}),
        },
        "create": {
            "request": {
                "method": "POST",
                "path": CREATE_PATH,
                "payload": create_payload,
            },
            "http_status": create_status,
            "response": create_body,
        },
        "final": {
            "request": {
                "method": "GET",
                "path": f"{GET_PATH}?verification_id={verification_id}",
            },
            "response": final,
        },
    }
    return _write_scenario(f"{vtype}__direct__{outcome}", doc)


def run_link(check: dict, outcome: str) -> Path:
    vtype = check["verification_type"]
    fields = deepcopy(check[outcome])
    create_payload = {
        "verification_type": vtype,
        "mode": "link",
        "send_email": False,
        "input_data": {
            "email": f"gov-registry-test+{vtype}-{outcome}@example.com",
            **fields,
        },
    }
    create_status, create_body = _request("POST", CREATE_PATH, create_payload)
    verification_id = None
    token = None
    submit_status = None
    submit_body = None
    submit_payload: dict[str, Any] = {}
    final = None

    if isinstance(create_body, dict):
        verification_id = (create_body.get("data") or {}).get("id")
        token = _token_from_link(create_body)

    if token and create_status in {200, 201}:
        # Fields were prefilled + locked at create; empty submit still triggers Korapay.
        submit_status, submit_body = _request(
            "POST",
            SUBMIT_PATH.format(token=token),
            submit_payload,
            auth=False,
        )
        if verification_id:
            final = _poll(str(verification_id))

    doc = {
        "scenario": {
            "verification_type": vtype,
            "mode": "link",
            "outcome": outcome,
            "source": "https://developers.korapay.com/docs/testing-your-integration",
            **({"note": check["fail_note"]} if outcome == "fail" and check.get("fail_note") else {}),
        },
        "create": {
            "request": {
                "method": "POST",
                "path": CREATE_PATH,
                "payload": create_payload,
            },
            "http_status": create_status,
            "response": create_body,
        },
        "submit": {
            "request": {
                "method": "POST",
                "path": SUBMIT_PATH.format(token=token or "<token>"),
                "payload": submit_payload,
            },
            "http_status": submit_status,
            "response": submit_body,
        },
        "final": {
            "request": {
                "method": "GET",
                "path": f"{GET_PATH}?verification_id={verification_id}",
            },
            "response": final,
        },
    }
    return _write_scenario(f"{vtype}__link__{outcome}", doc)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, Any]] = []
    total = len(CHECKS) * 4
    idx = 0
    for check in CHECKS:
        for mode in ("direct", "link"):
            for outcome in ("success", "fail"):
                idx += 1
                label = f"{check['verification_type']} / {mode} / {outcome}"
                print(f"[{idx}/{total}] {label} …", flush=True)
                try:
                    path = run_direct(check, outcome) if mode == "direct" else run_link(check, outcome)
                    raw = json.loads(path.read_text())
                    final_status = ((raw.get("final") or {}).get("response") or {}).get("data", {}).get("status")
                    create_http = (raw.get("create") or {}).get("http_status")
                    print(f"    -> {path.name} create={create_http} final_status={final_status}", flush=True)
                    summary.append(
                        {
                            "file": path.name,
                            "verification_type": check["verification_type"],
                            "mode": mode,
                            "outcome": outcome,
                            "create_http_status": create_http,
                            "final_status": final_status,
                        }
                    )
                except Exception as exc:  # noqa: BLE001 — collect and continue
                    print(f"    !! ERROR: {exc}", flush=True)
                    summary.append(
                        {
                            "verification_type": check["verification_type"],
                            "mode": mode,
                            "outcome": outcome,
                            "error": str(exc),
                        }
                    )

    summary_path = OUT_DIR / "_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nWrote {len(summary)} scenarios. Summary: {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
