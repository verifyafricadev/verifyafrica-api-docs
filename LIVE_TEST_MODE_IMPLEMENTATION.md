# Live / Test Mode Implementation

Customer-facing apps live on production domains only. A Live ↔ Test switcher changes which API the frontend talks to. Separate `test.*` frontend domains remain for **internal** staging deploys. `test.api.verifyafrica.io` stays as the test API forever.

## Goals

- One customer UX domain per app (`dashboard`, `admin`, `app`, `status`) with a Live / Test switcher.
- Separate data worlds: production DB ↔ test DB (already true today).
- Signup on Live immediately provisions a Test twin so users can try the product without KYC.
- Keep `test.dashboard` / `test.admin` / `test.app` / `test.status` for engineers pushing to Railway test without touching production frontends.

## Domain map

| Surface | Customer (prod frontend) | Internal staging | API |
|---------|--------------------------|------------------|-----|
| Dashboard | `dashboard.verifyafrica.io` | `test.dashboard.verifyafrica.io` | Live → `api.verifyafrica.io` / Test → `test.api.verifyafrica.io` |
| Admin | `admin.verifyafrica.io` | `test.admin.verifyafrica.io` | same |
| Hosted verify | Live → `app.verifyafrica.io` | `test.app.verifyafrica.io` | Test mode hosted links always use `test.app.*` |
| Status | `status.verifyafrica.io` | `test.status.verifyafrica.io` | mode-aware later if needed |

## Product rules

### Live mode

- Full product: KYC, real billing, Live API keys, Live webhooks, `app.verifyafrica.io` hosted links.
- Source of truth for customer passwords and account-security actions (change / forgot / reset / complete-temp).

### Test mode

- Full app functionality **except Live API keys** (show / use Test keys only).
- No KYC required to run verifications, use Test API keys, or invite (skip or auto-approve on test).
- Separate billing profile + wallet; **$20 Test Billing** credit on twin create / signup provision.
- Card top-ups stay blocked (existing `IS_TEST_ENVIRONMENT` behavior).
- Hosted verification links use **`test.app.verifyafrica.io`**.
- Account settings that mutate identity/security (change password, etc.) are **Live-only** in the customer UI. `test.*` password UI is internal-only / discouraged.

## Auth model

### Customer dashboard / admin on production hosts

1. User logs in against **production API** only (prod access + prod refresh cookie).
2. Switching to Test: frontend asks **prod** for a test access token. Prod RPC → test API mints access for the linked user.
3. Frontend calls `test.api` with that **Bearer access token** only (no test refresh cookie on the customer prod frontend).
4. When the test access token expires / 401: frontend hits **prod** again (`mint test access`); prod RPC → test. Single-flight re-mint to avoid stampedes.
5. If **prod refresh** is dead → full logout (even while viewing Test mode). User must log in again on Live.

### Internal `test.*` frontends

- Unchanged: normal login against `test.api` with test refresh cookies.
- Own session lifecycle; logout when test refresh dies.

### Token / storage implications (frontend)

- Mode store: `live` | `test`.
- API base URL switches with mode.
- TanStack Query keys prefixed with `live:` / `test:`; clear/invalidate on switch.
- Access token storage keyed by mode (today cookie prefix is host-derived — must become mode-aware on a single host).
- Only prod refresh cookie is used on production frontends.

## Identity linking

### `environment_link_id`

- UUID on **User** and **Tenant** in both environments.
- Same value on twins; all cross-env RPCs address twins by this id (never trust email from the browser).
- Set at provision time and by the one-time migration.

### Tenant email uniqueness

- `Tenant.email` is **unique** (normalized; blank stored as `NULL` so multiple empty values do not collide).
- Enables safe email-based matching during migration and clearer org identity going forward.

## Cross-env RPC (server-to-server)

Not a special protocol — HTTPS endpoints on each API, authenticated with a shared **service secret** (HMAC signature on body + timestamp, or equivalent). Only the peer environment may call them.

### Planned endpoints (test API is the main callee; prod may expose mirrors where needed)

| RPC | Direction | Purpose |
|-----|-----------|---------|
| `provision_twin` | prod → test | Create linked user + tenant + memberships + wallet + $20 + KYC skip/auto |
| `mint_access` | prod → test | Issue short-lived test access JWT for `environment_link_id` |
| `sync_password` | prod → test | Overwrite password hash; `bump_token_version` to revoke test sessions |
| `sync_membership` | prod → test | Mirror invite / role / remove after Live changes |
| `sync_profile` | prod → test | Overwrite allowed profile fields after Live profile updates |

Prod authorizes customer-triggered RPCs using the **prod session** (user must be authenticated on prod). The service secret authenticates prod-as-caller to test; the link id selects the subject.

### Password policy

- Prod is source of truth for customer passwords.
- Every Live password change / reset / complete-temp → `sync_password` + `bump_token_version` on test.
- Password changes performed on test (including `test.*`) do **not** sync back to prod.

## One-time migration

Prereq: prod DB snapshot taken for rollback.

### Match rules

1. **Users:** match by normalized email (unique on both sides).
2. **Tenants:** prefer match via membership graph after users are linked; tenant email is a strong hint once unique. Ambiguous pairs → conflict report, no auto-merge.

### On confident match (email)

Prod **overwrites** test profile fields only:

**User (safe):** `first_name`, `last_name`, `phone_number`, `avatar_url`  
**Tenant (safe):** `name`, contact `email`  
**Memberships:** roles / active flags from prod

**Never copy prod → test:**

- `stripe_customer_id`, wallets, billing rows  
- API keys, webhooks  
- KYC / compliance payloads  
- `slug`  
- verification / history data  
- raw password except via dedicated sync (copy hash when linking prod→test twins)

Assign the same `environment_link_id` on both sides.

### Prod-only

Create test twin (profile + memberships + password hash + $20 + KYC open). Set link ids.

### Test-only

Create prod twin with **random password** + `must_change_password=True`. Set link ids. User must change password on first Live login.

### Conflicts

Export a report; do not auto-merge. Resolve manually, then re-run.

### After cutover

Ongoing Live mutations keep test in sync via RPC (provision on signup, membership, password, profile). Migration alone is not enough.

## Signup / onboarding (new behavior)

1. Public signup remains on **Live** only.
2. After Live tenant+user create → RPC `provision_twin` on test.
3. User can switch to Test immediately and use the product without KYC.
4. Live still requires KYC for Live verifications / Live invites (existing gates).

## Admin app

- Same Live / Test switcher pattern on `admin.verifyafrica.io`.
- Internal testing continues on `test.admin.verifyafrica.io` against `test.api`.
- Superuser sessions follow the same mint-via-prod rules when using the production admin host.

## Frontend work (high level)

1. Mode provider + switcher UI (client + admin) + Test banner.
2. Dynamic API base URL; dual query-key prefix; invalidate on switch.
3. Mode-keyed access tokens; prod-only refresh; mint endpoint client helper with single-flight.
4. Hide / disable Live-only security settings while `mode === test`.
5. Hosted link builders: Test → `test.app`, Live → `app`.
6. API key screens: label and fetch key for active mode only.

## Backend work (phased)

1. **Schema:** unique `Tenant.email`; `environment_link_id` on User + Tenant. ✅ started (`users` migration `0044`)
2. **RPC layer:** service auth, mint access, sync password, provision twin ✅
3. **Wire Live password paths** to `sync_password`. ✅ change / complete-temp / reset
4. **Wire signup** to `provision_twin`. ✅ (+ lazy provision on Test switch if unlinked)
5. **Migration command** with dry-run + apply + conflict report. ⏳
6. **Test-env product gates:** skip KYC for verifications when `IS_TEST_ENVIRONMENT` (or auto-approve twins). ⏳
7. **Frontend** mode switcher (client, then admin). ✅ shell UI + HTTP plumbing

### Implemented so far (code)

- Doc: this file
- `Tenant.email` → nullable + **unique** (blanks → `NULL`; duplicates rewritten in migration)
- `User.environment_link_id` / `Tenant.environment_link_id` (unique, nullable UUID)
- HMAC RPC: `users/cross_env/` (`signing`, `client`, `permissions`, views)
  - `POST /api/v2/internal/cross-env/mint-access/`
  - `POST /api/v2/internal/cross-env/sync-password/`
  - `POST /api/v2/internal/cross-env/provision-twin/` (create/update Test twin)
  - `POST /api/v2/users/test-mode/access-token/` (prod session → provision if needed → peer mint)
  - Live signup `on_commit` → best-effort `provision_twin`
- Env: `CROSS_ENV_RPC_SECRET`, `CROSS_ENV_PEER_API_BASE_URL`, `CROSS_ENV_RPC_MAX_SKEW_SECONDS`
- Password change / complete-temp / reset call `sync_password_to_peer` (best-effort)
- **Frontend (client + admin)**
  - Live/Test switcher in sidebar footer + Test banner when active
  - Mode store; dynamic API base URL; test access via mint (no test refresh on prod hosts)
  - Query keys scoped with mode (client org queries); cache cleared on switch
  - Test mode: hide KYC nav + redirect; hide Change Password; billing/API key labels follow mode
  - Hosted verify links resolve via active mode (`test.app.*` in Test)
  - Switcher **only** on production customer hosts; disabled on local/dev and `test.*`

## Explicit non-goals

- Merging production and test databases into one.
- Removing `test.api` or internal `test.*` frontends.
- Proxying all Test API traffic through prod (browser talks to `test.api` with minted access tokens).
- Syncing password changes from test → prod.

## Open ops checklist

- [x] Shared RPC secret wired for Lightsail prod (GitHub `Prod Secrets`: `CROSS_ENV_RPC_SECRET`, peer URL vars). Still set the **same** secret on Railway test.
- [ ] Shared RPC secret + peer URL on Railway test (`CROSS_ENV_PEER_API_BASE_URL=https://api.verifyafrica.io`).
- [ ] CORS: production frontends allowed on `test.api` for Bearer calls.
- [ ] Migration dry-run on copies; apply with snapshot rollback plan.
- [ ] Confirm Railway test `ENVIRONMENT=development` still grants $20 (or switch grant to `IS_TEST_ENVIRONMENT`).
- [ ] Redirect or document old customer habits of using `test.dashboard` for day-to-day (optional later).

## Decisions log

| # | Decision |
|---|----------|
| 1 | Twin link via `environment_link_id` + service secret; prod session authorizes mint. |
| 2 | Customer frontend: prod refresh only; test access via prod→test RPC; dead prod refresh → logout. `test.*` keeps own refresh. |
| 3 | One-time migration; on email match prod overwrites allowed test profile fields; tenant email made unique. |
| 4 | Prod password SoT; RPC hash sync + `bump_token_version` on test. |
| 5 | Full Test app except Live keys; $20 test wallet; separate billing; Test hosted links on `test.app.*`. |
