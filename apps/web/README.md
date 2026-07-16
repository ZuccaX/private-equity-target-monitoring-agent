# PE Origination Agent Web App

Next.js 16 and React 19 frontend for the Private Equity Origination Agent
Platform. For the product overview and full-stack setup, start with the
[English README](../../README.md) or
[Chinese README](../../README_ZH.md).

This file documents the frontend package only. It is not the implementation
specification; milestone scope and evidence remain in
[`docs/`](../../docs/FINAL_IMPLEMENTATION_PLAN.md).

## Prerequisites

- Node.js
- pnpm 10.13.1
- the FastAPI service running locally (default: `http://localhost:8000`)

## Configuration

Create an ignored `apps/web/.env.local` file if the API uses a non-default URL.
Today the only frontend variable is:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Do not commit `.env.local`. Without this variable, the client defaults to
`http://localhost:8000`.

## Run locally

```bash
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Routes

| Route | View |
|---|---|
| `/` | Dashboard summary and recent workflow activity |
| `/companies` | Target company pipeline |
| `/companies/[companyId]` | Company context, CRM, documents and RAG |
| `/news-articles` | Ingested company news |
| `/triggers` | Extracted business triggers |
| `/crm` | Contacts and CRM interactions |
| `/documents` | Internal document list and preview |
| `/rag` | Company-scoped retrieval explorer |
| `/agent-runs` | Agent workflow history |
| `/drafts` | Editable outreach drafts and review state |

The backend also exposes mandate, pipeline, feedback, audit and run-step APIs,
but dedicated frontend pages for those modules are not part of the verified M3
snapshot.

## Source structure

```text
src/app/          App Router pages and layouts
src/components/   Product sections and reusable UI components
src/lib/api.ts    Typed FastAPI client and response contracts
src/lib/utils.ts  Shared styling helper
```

`src/lib/` is application source and must remain tracked. The repository root
ignore rules explicitly protect it from broad Python packaging patterns.

## Validation

```bash
pnpm lint
pnpm exec tsc --noEmit
pnpm build
```

The production build is offline-safe and uses local system font stacks. The M3
checkpoint passed lint, TypeScript and production generation for all 12 routes.
A dedicated frontend component/browser automation suite has not yet been added;
backend integration tests and live HTTP/Compose checks cover the current API/UI
boundary.

## Backend dependency and errors

Most pages load data from `NEXT_PUBLIC_API_BASE_URL`. A visible `Failed to
fetch` message normally means the API is stopped, unreachable, blocked by CORS,
or connected to a database that has not been migrated. Check:

- API: `http://localhost:8000/health`
- readiness: `http://localhost:8000/ready`
- OpenAPI: `http://localhost:8000/docs`

Never place database credentials or private API keys in frontend environment
variables: every `NEXT_PUBLIC_*` value is exposed to the browser.
