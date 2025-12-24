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

## Phase 2 – Parsing & Review Loop [COMPLETED] ✅

**Goal:** Assist the user, never override them.

### Backend
- [x] PDF parsing service with pdfplumber
- [x] Regex patterns for Type C and Type E invoices
- [x] Confidence scoring per field (0.0 to 1.0)
- [x] `invoice_parse_attempt` table persistence
- [x] Auto-parsing on upload
- [x] Status updates based on confidence (PARSED ≥0.7, NEEDS_REVIEW <0.7)
- [x] Performance benchmarking (~0.3s parse time)

### Frontend
- [x] Parse attempts API endpoint
- [x] Parsed data display in detail view
- [x] "Copy All to Form" button for bulk accept
- [x] Auto-calculation trigger after copying parsed data
- [x] Confidence badge display
- [x] Status badges hidden when invoice is locked

### Definition of done
- [x] Parsing never mutates locked data
- [x] All attempts are auditable
- [x] User has explicit control over accepting parsed data
- [x] Type-safe interfaces for parsed data

**Completed:** 2025-12-24

---

## Phase 3 – Monotributo Tracking [IN PROGRESS] 🚧

**Goal:** Prevent category overruns.

### Slice 1: Category Management [COMPLETED] ✅

**Backend**
- [x] Monotributo category version and limit models
- [x] Database schema with versioning support (version_id, valid_from, valid_to)
- [x] ARCA web scraper (requests + BeautifulSoup)
- [x] Parse all category fields (income limits, physical limits, monthly payments)
- [x] GET endpoint for current categories
- [x] POST endpoint to update from ARCA with change detection
- [x] Version comparison logic (detects data changes)
- [x] Auto-increment version names (2025-v1 → 2025-v2)

**Frontend**
- [x] TypeScript schemas for Monotributo data
- [x] Categories page (`/monotributo`) with four sections:
  - Annual income limits (services/goods)
  - Physical/consumption limits (surface, electricity, rent)
  - Monthly payments - services
  - Monthly payments - goods
- [x] "Update from ARCA" button with status messages
- [x] Version badge and validity date display
- [x] Navigation links between pages
- [x] Argentine locale formatting (ARS currency, numbers)

**Completed:** 2025-12-24

### Slice 2: Usage Tracking [PENDING]

**Features**
- Rolling 12-month calculations
- Usage percentage + remaining margin
- Link invoices to category versions

**UI**
- Traffic-light status indicators
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

## Known Issues & Technical Debt

### Critical (Audit-Safety)
- **FX Rate Date Bug**: Currently `fx_date` defaults to current date instead of invoice issue date. This breaks the snapshot philosophy - exchange rates must reflect the rate **at the time the invoice was issued**, not when it was uploaded. Fix: Auto-set `fx_date` to `issue_date` when user doesn't provide it.

### Nice-to-Have
- ARCA version date parsing (currently uses fetch date as fallback)

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
