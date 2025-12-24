# 🗺️ Tevildo – Project Roadmap

This roadmap translates Tevildo’s **design and architecture** into an ordered, low-risk execution plan.

It is intentionally conservative, local-first, and optimized for correctness over speed — while still being **reproducible across machines** via Docker for the backend.

---

## Guiding Principles

- Build **vertically**, not horizontally
- Each phase must leave the app in a **usable, coherent state**
- Prefer **manual correctness** before automation
- Avoid speculative features
- Keep everything **audit-safe** and explainable

---

## Phase 0 – Foundations (Blocking) [COMPLETED] ✅

**Goal:** Make the project safe to evolve, and trivial to run on any machine.

### Backend
- [x] FastAPI project scaffold
- [x] Application settings & config loading
- [x] Local filesystem layout (`data/`, `invoices/`)
- [x] SQLite connection with foreign keys enabled

### Docker (Backend)
- [x] `backend/Dockerfile` for the FastAPI runtime
- [x] `docker-compose.yml` for local development
- [x] Bind-mount persistent app data (DB + PDFs):
  - `./backend/data:/app/data`
- [x] Env var convention:
  - `TEVILDO_DATA_DIR=/app/data`

### Database
- [x] SQLAlchemy models aligned with `DATABASE.md`
- [x] Alembic setup
- [x] Initial migration (baseline schema)

### Definition of done
- [x] App starts locally (via Docker)
- [x] Database can be created from scratch via migrations
- [x] Persistent data survives container restarts (volume/bind mount)
- [x] No business logic yet

**Completed:** 2025-12-21

---

## Phase 1 – Invoice Ingestion (MVP) [COMPLETED] ✅

**Goal:** Replace spreadsheets with a trusted source of truth.

### Backend
- [x] Upload invoice PDF endpoint
- [x] Persist `stored_file` with SHA256 hash
- [x] Create `invoice` in `UPLOADED` state
- [x] Pydantic schemas for type-safe API responses
- [x] Invoice list endpoint (GET /api/invoices) with pagination
- [x] Invoice delete endpoint (DELETE /api/invoices/{id})
- [x] Invoice detail endpoint (GET /api/invoices/{id})
- [x] Invoice PDF serving endpoint (GET /api/invoices/{id}/pdf)
- [x] Invoice update endpoint (PUT /api/invoices/{id})
- [x] Invoice lock endpoint (POST /api/invoices/{id}/lock)

### Frontend
- [x] Next.js 16 setup with App Router
- [x] shadcn/ui + Tailwind CSS v4
- [x] Upload page with file picker
- [x] Invoice list page with table
- [x] Status badges with color coding
- [x] Navigation between upload and list pages
- [x] Delete functionality with confirmation dialog
- [x] Invoice detail / edit screen with PDF viewer
- [x] React Hook Form + Zod validation
- [x] Auto-calculation for currency conversion (fx_rate × total_original = total_ars)
- [x] Locked status indicators in list and detail views

### Definition of done
- [x] User can upload PDFs via web UI
- [x] User can see list of uploaded invoices
- [x] User can manually input all invoice data
- [x] Totals and dates persist correctly
- [x] User can lock invoice snapshot

**Completed:** 2025-12-24

---

## Phase 2 – Parsing & Review Loop

**Goal:** Assist the user, never override them.

### Features
- PDF parsing service
- `invoice_parse_attempt` persistence
- Confidence + warnings
- `NEEDS_REVIEW` workflow

### UI
- Side-by-side parsed vs manual fields
- Explicit user confirmation

### Definition of done
- Parsing never mutates locked data
- All attempts are auditable

---

## Phase 3 – Monotributo Tracking

**Goal:** Prevent category overruns.

### Features
- Category version management
- Category limits per version
- Rolling 12-month calculations
- Usage percentage + remaining margin

### UI
- Traffic-light status
- Historical category context

### Definition of done
- Correct calculations for past and current invoices
- Historical reports remain stable after category changes

---

## Phase 4 – Reports & Exports

**Goal:** Accountant-ready outputs.

### Features
- Excel summary report
- ZIP export with PDFs grouped by month
- Full local backup export

### Definition of done
- Accountant can work without re-processing data
- Exports are reproducible

---

## Phase 5 – Quality & Polish

**Goal:** Make it pleasant and safe to use long-term.

- Validation & error handling
- UI refinements
- Import/export edge cases
- Performance cleanup (only if needed)

---

## Explicitly Deferred (Non-Goals)

- ARCA / AFIP integration
- Multi-user support
- Cloud sync
- Mobile-first UX
- Automated invoice issuance

---

## Roadmap Philosophy

If a feature:
- risks auditability
- adds operational complexity
- or reduces clarity

…it does **not** belong in Tevildo.
