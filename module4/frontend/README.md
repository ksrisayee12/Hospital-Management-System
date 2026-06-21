# Healthcare Governance & Security Intelligence Platform — Frontend

React + Vite implementation of the 5-page Governance Intelligence Platform
(Module 4 frontend), built from the design brief: Command Center,
Investigations, Trust & Risk, Governance Ledger, Network Analytics.

## Run locally

```bash
npm install
npm run dev
```

Opens at `http://localhost:5173`.

## Structure

```
src/
├── styles/
│   ├── tokens.css       Design tokens — every color/space/radius lives here
│   └── globals.css      Resets + base typography
├── components/
│   ├── primitives/      StatusBadge, MetricCard, TrendCard, Timeline,
│   │                    AlertCard, InvestigationCard, HospitalCard,
│   │                    TrustCard, EmptyState, AnalyticsPanel,
│   │                    ChartContainer, DetailInspector, SearchCommand
│   └── layout/          AppShell, TopNavigation, PageHeader, HeroBanner
├── pages/                One file per nav item (Command Center, etc.)
├── data/mockData.js      Mock data shaped exactly like the real backend's
│                         API responses — swap for fetch() calls 1:1
└── App.jsx               Simple state-based router between the 5 pages
```

## Connecting to the real backend

Every shape in `data/mockData.js` mirrors a Pydantic schema from the
Module 4 backend (`schemas/*.py`). To connect:

1. Replace the static imports in each page with a `useEffect` + `fetch`
   call to the matching endpoint (`GET /api/v1/alerts`, `GET
   /api/v1/complaints`, etc.)
2. Add the JWT bearer token from your auth flow to each request.
3. The shapes should match exactly — if a field is missing or renamed,
   that's a real integration bug to fix, not a frontend bug to paper over.

## Design tokens

All colors, spacing, radii, and type sizes are CSS custom properties in
`src/styles/tokens.css`. Never hardcode a hex value in a component — add
or reuse a token instead, so a future rebrand only touches one file.
