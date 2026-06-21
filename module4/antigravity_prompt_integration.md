# ANTIGRAVITY BUILD PROMPT — Module 4: Wire Backend ↔ Frontend Into a Real Application

## 0. WHO YOU ARE WORKING FOR

I'm one of four developers on a hackathon team building the
**Patient-Sovereign, Signature-Verified Prescription Intelligence Network**.
I own **Module 4: Governance & Security Intelligence**. The other three
modules (Identity & Consent, Patient Vault, Doctor Clinical Intelligence)
are owned by teammates. Module 1 (Identity & Consent) already has a real
auth system issuing real JWTs — you will need to read its actual code to
learn the exact contract (claim names, algorithm, secret-sharing
mechanism) rather than guessing. Do not redesign or rebuild Modules 1–3;
only integrate against what they already expose.

## 1. WHAT ALREADY EXISTS

**Backend**: a FastAPI app implementing Module 4 — audit logging, a
SHA-256 hash-chain ledger, fraud detection, trust scoring, complaint
management, emergency override workflow, and hospital risk analytics. It
has 7 SQLAlchemy models, Pydantic schemas, and ~8 route groups. It was
built and functionally tested against SQLite as a local stand-in, but the
**real target database is Supabase Postgres**, and a Supabase project has
now been created — I'll provide the connection string / anon key and
project URL in the workspace or chat. Important: **I do not know what
tables, if any, currently exist in that Supabase project.** Do not assume
it's empty, and do not assume it already matches Module 4's models.

**Frontend**: a React + Vite app implementing 5 pages (Command Center,
Investigations, Trust & Risk, Governance Ledger, Network Analytics) with
13 reusable primitives and a design-token system. It currently runs
entirely on static mock data in `src/data/mockData.js`, shaped to mirror
the backend's Pydantic response schemas. It has known visual/responsive
issues that are **explicitly out of scope for this task** — do not do a
design pass; only touch frontend code where wiring it to the real backend
requires it.

Both currently exist as separate, unconnected codebases sitting in the
workspace. Your job is to make them work together as one real, running
application.

## 2. THE ACTUAL JOB: END-TO-END WIRING

This is an integration task, not a feature-building task. Work in this
order and do not skip the inspection steps — guessing instead of
inspecting is the most likely way this goes wrong.

### 2.1 Inspect before touching anything

- [ ] Read Module 1's actual auth implementation (wherever it lives in the
  workspace) to find: the JWT signing algorithm, the exact claim names
  used for user id and role (Module 4's code currently assumes `sub` and
  `role`, plus an optional `hospital_id` — confirm this matches reality;
  if it doesn't, Module 4's `core/auth.py` is wrong and must be corrected
  to match Module 1, not the other way around), and how the signing
  secret is shared between modules (env var name, secrets file, etc).
  Report exactly what you find before changing anything.
- [ ] Connect to the Supabase project with the credentials I provide and
  list every table that currently exists. Do not assume which of Module
  4's 7 tables (`audit_logs`, `ledger_events`, `complaints`,
  `security_alerts`, `trust_scores`, `hospital_metrics`,
  `emergency_overrides`) already exist, already exist under different
  names, or don't exist at all. Also check whether tables from Modules
  1–3 already exist (e.g. a `profiles` or `doctors` table) since Module
  4's foreign-key-like string columns (`doctor_id`, `patient_id`,
  `hospital_id`) need to reference real identifiers that those tables
  actually produce — report the real ID format you find (UUID? serial
  int? custom string code like "DOC001"?) since Module 4's current code
  assumes loose string IDs and may need adjusting if reality differs.
- [ ] Report back a short summary of both findings before proceeding to
  migrations. If something is ambiguous or missing (e.g. no Module 1
  table exists yet to reference), ask me rather than inventing a shape.

### 2.2 Get the schema live on Supabase

- [ ] Initialize Alembic against Module 4's `Base.metadata` if not already
  done, generate the migration(s) needed to reach the full 7-table
  schema, and run them against the real Supabase Postgres instance using
  the credentials provided. If tables with conflicting names/shapes
  already exist from a teammate's earlier experiment, do not silently
  drop or overwrite them — stop and ask me.
- [ ] Confirm `DATABASE_URL` in Module 4's `.env` is set to the real
  Supabase connection string (using the **pooled connection string** if
  Supabase provides one for serverless/Edge-style connections, or the
  direct connection string if running as a long-lived process — pick
  correctly based on how Module 4 will actually be deployed, and state
  which you chose and why).
- [ ] Run Module 4's existing functional test flow (complaint → trust
  penalty → ledger entry → tamper detection → fraud alert → override
  approval → hospital risk scoring) against the live Supabase database,
  not SQLite, and confirm it still passes. This is the most important
  checkpoint in the whole task — a UUID-handling bug was already found
  and fixed once when moving off SQLite assumptions; re-verify there
  isn't a second one now that this is real Postgres over the network
  instead of a local file.

### 2.3 Wire the frontend to the real backend

- [ ] Add an API client layer to the frontend (`src/lib/api.js` or
  similar — your call on exact structure) that wraps `fetch` against
  Module 4's base URL, attaches the JWT bearer token, and centralizes
  error handling. Don't scatter raw `fetch` calls across every page
  component.
- [ ] For auth: since Module 1 issues the real JWT, the frontend needs to
  actually receive and store that token (likely from Module 1's
  login/auth UI or endpoint — find out how, don't invent a parallel auth
  flow). If Module 1's frontend doesn't exist yet or isn't reachable in
  this workspace, build the minimal thing needed to acquire a real token
  for testing Module 4 (e.g. a dev-only token input field, or a direct
  call to Module 1's login endpoint if it exists) — but make this clearly
  marked as a temporary dev affordance, not a permanent parallel login
  system.
- [ ] Replace every import from `src/data/mockData.js` across all 5 pages
  with real data fetched from the corresponding Module 4 endpoint:
  - Command Center → `GET /alerts`, `GET /complaints`, `GET /emergency`
    (filtered/combined client-side for the Attention Center groupings)
  - Investigations → same three endpoints, unified into the master list
  - Trust & Risk → `GET /trust-score`
  - Governance Ledger → you'll need a `GET /ledger` list endpoint, which
    **does not currently exist** — Module 4 only has `GET /ledger/verify`.
    Add a paginated list endpoint that returns ledger events for the
    timeline view (reuse the existing `LedgerEventOut` schema), then wire
    the frontend's "Verify chain integrity" button to the real
    `GET /ledger/verify` endpoint instead of its current fake
    setTimeout-based mock.
  - Network Analytics → `GET /hospital-risk`
- [ ] Every list endpoint needs pagination wired into the frontend if the
  backend has it (check; if it doesn't yet, that's a real gap — add
  basic `limit`/`offset` support to both sides rather than fetching
  unbounded result sets).
- [ ] Loading and error states: every page currently renders instantly
  because mock data is synchronous. Real network calls aren't. Add
  loading skeletons or spinners (reuse `EmptyState` styling conventions
  if sensible, or add a minimal `LoadingState` primitive) and visible
  error states (don't let a failed fetch silently render an empty page —
  the person needs to know the request failed, not just see nothing).
- [ ] Resolution actions in Investigations (Escalate / Mark resolved /
  Dismiss) currently mutate local mock state only. Wire them to real
  mutating endpoints: complaint status → `PATCH /complaints/{id}`, alert
  status → `PATCH /alerts/{id}`, override approval →
  `POST /emergency/{id}/approve`. After a successful mutation, refetch or
  optimistically update — pick one approach and apply it consistently
  across all three.

### 2.4 CORS, environment, and deployment sanity

- [ ] Confirm Module 4's CORS config in `main.py` (currently wide open
  `allow_origins=["*"]`) actually works against the frontend's real dev
  origin (`http://localhost:5173` or wherever Vite serves it) and tighten
  it to that specific origin for local dev, with a clear comment on what
  needs to change before any real deployment.
- [ ] Add a `.env.example` on the frontend side documenting the API base
  URL variable it needs (e.g. `VITE_API_BASE_URL`), and confirm the
  frontend actually reads from an env var rather than a hardcoded
  `localhost` string, so this doesn't silently break when deployed.
- [ ] Confirm `GET /health` on the backend (already extended to check DB
  connectivity per earlier work — verify this is still true) is reachable
  from the frontend and consider surfacing a simple connection-status
  indicator somewhere in the UI (the existing `HeroBanner` "All systems
  monitored" badge on Command Center is a natural place — wire it to
  reflect real health-check status instead of being a static string).

## 3. EXPLICIT NON-GOALS

- Do not redesign any frontend page's layout, spacing, or visual styling.
  If a genuine wiring need forces a small structural change (e.g. a
  component needs a `loading` prop it didn't have before), make the
  minimal change required and note it — don't take this as license for a
  broader design pass.
- Do not build Module 1, 2, or 3. Only integrate against what they
  actually expose today, and ask me if something they're supposed to
  expose doesn't exist yet.
- Do not invent a new auth system. Module 1's JWT is the one source of
  truth for identity in this entire platform.
- Do not silently change Module 4's existing business logic (trust score
  math, fraud thresholds, ledger hash chain) while wiring — if wiring
  reveals an actual bug in that logic, report it and fix it explicitly,
  don't quietly tweak it.

## 4. WHAT "DONE" LOOKS LIKE

1. A written report of what you found in the 2.1 inspection (Module 1's
   real JWT shape, Supabase's real existing tables, real ID formats) —
   before any code changes, so I can sanity-check it.
2. `alembic upgrade head` run successfully against the live Supabase
   instance, with a list of exactly which tables now exist.
3. The full functional flow (complaint → trust penalty → ledger entry →
   tamper detection → fraud alert → override approval → hospital risk
   scoring) passing against live Supabase, not SQLite.
4. All 5 frontend pages rendering real data from the real backend, with
   visible loading and error states, and the 3 Investigations actions
   actually mutating real backend data through to a refetch.
5. A new `GET /ledger` endpoint added (since it didn't exist), documented
   alongside the rest of the API in the backend's README.
6. A short list of anything you had to ask me about along the way and how
   it was resolved, plus anything you flagged but did NOT change because
   it touched a non-goal area.

Ask me immediately, before writing code, if: Module 1's JWT contract
doesn't match what Module 4 currently assumes; the Supabase project
already contains conflicting tables; or you can't find a way to obtain a
real JWT for testing because Module 1's login flow isn't reachable in this
workspace. Don't guess on any of these three — they're foundational to
everything else in this task.
