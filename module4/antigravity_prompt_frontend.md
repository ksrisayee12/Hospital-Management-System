# ANTIGRAVITY BUILD PROMPT — Module 4 Frontend: Governance & Security Intelligence Platform

## 0. WHO YOU ARE WORKING FOR

I'm one of four developers on a hackathon team building the
**Patient-Sovereign, Signature-Verified Prescription Intelligence Network**
— a patient-owned healthcare data platform. I own **Module 4: Governance &
Security Intelligence**, including both its FastAPI backend (already built
separately) and this React frontend. The other three modules (Identity &
Consent, Patient Vault, Doctor Clinical Intelligence) are out of scope —
don't touch them. I'm connecting this frontend to my backend separately
later; for now your job is to make the frontend itself as close to
flawless as possible standing alone.

## 1. PROJECT CONCEPT (context only, don't redesign this)

Patients own their medical data; every access requires signed consent and
is logged immutably. My module is the trust/audit/fraud layer that makes
the other three modules accountable: it tracks doctor trust scores, runs
fraud detection on access patterns, manages patient complaints and
emergency-override approvals, and maintains a tamper-evident hash-chain
ledger of every critical action platform-wide.

## 2. CURRENT STATE (already built — READ FIRST, DO NOT REWRITE FROM SCRATCH)

A working React + Vite app already exists at the path I'll give you in the
workspace. It builds cleanly (`npm run build` succeeds, zero errors) and
runs (`npm run dev`). Structure:

```
src/
├── styles/tokens.css        Design tokens — EVERY color/space/radius
├── styles/globals.css       Resets, base typography, focus states
├── components/primitives/   13 reusable UI primitives (see list below)
├── components/layout/       AppShell, TopNavigation, PageHeader, HeroBanner
├── pages/                   5 pages, one per nav item
├── data/mockData.js         Mock data shaped EXACTLY like the real backend's
│                            Pydantic schemas — this is the integration contract
└── App.jsx                  State-based router between the 5 pages
```

The 5 pages, exactly as specified in the original design brief — **do not
add, remove, or rename pages or top-nav items**:
1. **Command Center** — hero, KPI metrics, Attention Center (3-column:
   critical alerts / pending complaints / emergency requests), Recent
   Activity timeline, Threat Feed
2. **Investigations** — master-detail workspace (360px list + detail
   inspector), unified across alerts/complaints/emergency requests, with
   filter pills
3. **Trust & Risk** — Trust Leaderboard, Trust Distribution (pie),
   Risk Analysis (horizontal bars), Historical Trends (line chart)
4. **Governance Ledger** — visual hash-chain block timeline (NOT a table,
   per the brief) + Event Inspector showing hash/previous-hash/integrity
5. **Network Analytics** — Hospital Overview cards, Comparative Risk bar
   chart, three TrendCards (risk/complaints/trust)

13 primitives already built: `StatusBadge`, `MetricCard`, `TrendCard`,
`TimelineItem`/`TimelineFeed`, `AlertCard`, `InvestigationCard`,
`HospitalCard`, `TrustCard`, `EmptyState`, `AnalyticsPanel`/`ChartContainer`,
`InspectorPanel`/`InspectorSection`/`InspectorRow`, `SearchCommand`.

Design tokens already encode the brief's exact palette: background
`#F8FAFC`, card `#FFFFFF`, border `#E2E8F0`, primary `#2563EB`, success
`#10B981`, warning `#F59E0B`, danger `#EF4444`, purple accent `#8B5CF6`,
plus a full spacing/radius/type scale. **Do not introduce new brand colors
or bypass tokens with hardcoded hex values** — extend `tokens.css` if a
genuinely new semantic need arises, and say explicitly why.

Known constraints from the brief — do not relitigate:
- No large sidebar. Top nav only, workflow-style, not a page tree.
- No dense data tables on the Governance Ledger — visual block-chain
  storytelling instead.
- Calm visual hierarchy — colors are functional signals, not decoration.
- Inspiration register: Stripe/Linear/Notion/Vercel/Apple Health/Arc.
  Explicitly NOT AdminLTE/ERP/legacy hospital software/SOC-dashboard/
  cyberpunk.

## 3. YOUR TASK: FINETUNE TO PRODUCTION QUALITY

Everything below assumes the mock-data version stays mock for now — I'm
wiring the real backend separately. Do not invent fetch calls; focus on
making the frontend itself airtight, polished, and complete.

### 3.1 Visual + interaction audit (do this FIRST)

- [ ] Render every one of the 5 pages and actually look at them (take
  screenshots if your environment supports it). For each page, check
  against its "Purpose" question from the brief — does the page visibly
  answer that question within 2 seconds of looking at it, or is something
  buried/unclear?
- [ ] Check every inline `style={{...}}` block for spacing consistency.
  The brief demands generous whitespace and a breathing layout — flag any
  component that feels cramped relative to its neighbors and fix the
  spacing token used, not by guessing a new pixel value.
- [ ] Verify responsive behavior down to a 768px and 480px viewport for
  every page. Currently layouts use fixed CSS grid columns
  (`repeat(4, 1fr)`, `repeat(3, 1fr)`, `360px 1fr`, etc.) with NO media
  query fallback — this will break badly on tablet/mobile. Add proper
  responsive collapse (e.g. 4-col KPI grid → 2-col → 1-col; the
  Investigations master-detail 360px+1fr layout needs a stacked mobile
  fallback where selecting a list item pushes the detail view in, not
  squeezes both into an unusable sliver).
- [ ] Confirm every interactive element (`<button>`, clickable card) has a
  visible hover state, not just the existing `:focus-visible` token. Add
  hover styles using the existing token system — don't invent new colors.
- [ ] Confirm keyboard navigation works: Tab through each page in order,
  confirm focus is never lost into nowhere (e.g. confirm the
  `InvestigationCard` list and `TrustCard` rows are keyboard-reachable,
  not just mouse-clickable).
- [ ] Check `prefers-reduced-motion` is respected everywhere — the token
  file disables animations globally already, but verify no component
  uses an inline transition that bypasses this.

For each issue found, fix it and note what was wrong and why, in the same
style as a real code review — don't silently batch-fix without saying so.

### 3.2 Missing interactivity to add

The current build is intentionally static (state lives in local
`useState`, nothing persists, no real actions fire). Make these
interactions real within the mock-data world, without inventing a backend
connection:

- [ ] **Investigations resolution actions** (`Escalate` / `Mark resolved`
  / `Dismiss` buttons) currently do nothing. Wire them to update local
  state (`mockComplaints`/`mockAlerts`/`mockOverrides` arrays via React
  state, not the raw imported constants) so clicking them visibly changes
  the item's status badge and removes/reorders it in the list as
  appropriate. This should feel real even before the backend is wired.
- [ ] **Governance Ledger "Verify chain integrity" button** currently
  fakes a 900ms delay then always returns `valid: true`. Add a second
  demo state: occasionally (or via a hidden dev toggle) show the
  `broken_at_sequence` failure case too, so the page can demonstrate BOTH
  outcomes for a judge demo, not just the happy path.
- [ ] **SearchCommand** opens a modal but `onSearch` does nothing
  meaningful. Wire it to do a real (if simple) client-side filter across
  the mock alerts/complaints/doctors/hospitals datasets and show matching
  results inside the modal, grouped by type.
- [ ] **Trust & Risk page**: add a way to click a `TrustCard` row and see
  more detail — at minimum, expand inline to show a short trust-score
  history sparkline for that doctor (reuse `TrendCard`'s chart
  internals or extract a shared `Sparkline` primitive if duplicating
  becomes ugly — your call, but justify whichever you pick).
- [ ] **Network Analytics hospital cards**: clicking one should do
  something — at minimum, scroll-to/highlight that hospital in the
  Comparative Risk chart below. A full drill-down page is out of scope.

### 3.3 New primitives needed

- [ ] **`Sparkline`** (if not folded into TrendCard per 3.2) — a minimal
  inline trend line with no axes, for embedding inside list rows.
- [ ] **`ConfirmDialog`** — Investigations resolution actions are
  destructive-ish (escalating or dismissing a security alert is a real
  decision); add a lightweight confirm step before committing the action,
  styled consistently with `SearchCommand`'s modal treatment.
- [ ] **`Toast`** — after a resolution action succeeds, show a brief
  toast confirmation ("Alert escalated.", "Complaint marked resolved.")
  rather than a silent state change — per the writing guidance, the
  button's action name and the confirmation message should match exactly.

### 3.4 Copy pass

- [ ] Read every visible string in the app against the writing principles
  already encoded in the design brief's spirit: active voice, plain
  verbs, no filler, name things by what the user controls. Flag and fix
  any string that's vague, system-centric, or apologetic (e.g. if an
  empty state ever says something like "Oops, nothing to show," rewrite
  it as a direct, actionable statement in the interface's voice).
- [ ] Confirm the vocabulary is consistent across pages: e.g. if
  Investigations calls something a "Complaint" everywhere, the Command
  Center's Attention Center must use the exact same word, not a synonym.

### 3.5 Code quality pass

- [ ] Every component currently uses inline `style={{...}}` objects. This
  was a deliberate choice for a fast hackathon build with zero CSS-class
  collision risk — keep this pattern, don't introduce CSS Modules,
  styled-components, or Tailwind, unless you have a specific, stated
  reason tied to a real problem you hit (e.g. a measurable performance
  issue from inline style object recreation on every render — and if so,
  fix it with `useMemo` on the style object, not a framework swap).
- [ ] Check for any prop-drilling that's gotten awkward (e.g. if
  `selectedId` state in `InvestigationsPage` or `GovernanceLedgerPage`
  needs to reach three levels deep, consider whether a small local
  context or a colocated reducer would be cleaner — but only refactor if
  it's actually messy today, not preemptively).
- [ ] Run a final `npm run build` and confirm zero errors/warnings beyond
  the expected recharts chunk-size notice. Report the final build output.

## 4. WHAT "DONE" LOOKS LIKE

1. A written list of every issue found in 3.1, with before/after for each.
2. All five interactions in 3.2 working against mock data, demonstrable
   by clicking through the running `npm run dev` app.
3. The 2–3 new primitives from 3.3, used consistently (no one-off ad hoc
   modals or toasts duplicating what the new primitive does).
4. A copy pass summary — what changed and why, not just a diff.
5. `npm run build` succeeding with the same or better output as the
   current baseline (609 kB main bundle, 169 kB gzipped — flag clearly if
   your changes meaningfully increase this and explain why it was
   necessary).

Do not ask me about the backend integration, the other three modules, or
the overall project concept — section 1 and 2 are all the context you
need. DO ask me if you hit a genuine design ambiguity that the original
brief doesn't resolve (e.g. exact mobile breakpoint behavior for the
Investigations master-detail layout), rather than guessing silently on
anything that materially changes the page's structure.
