# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Tevildo** is a local-first personal application for tracking invoicing and income for Argentine *Monotributo* taxpayers. It helps prevent category overruns by maintaining an auditable record of invoices, exchange rates, and accumulated income.

**Critical Design Principle:** Auditability over automation. Every invoice preserves the exact exchange rate used, and historical data must remain immutable and explainable.

## Tech Stack

- **Backend:** FastAPI (Python) + SQLite + SQLAlchemy + Alembic
- **Frontend:** Next.js (App Router) + shadcn/ui
- **Deployment:** Docker (backend), local-first architecture
- **Processing:** pdfplumber, pypdf, Tesseract (OCR), openpyxl

## Development Commands

### Quick Start

**First time setup:**
```bash
make up          # Start services (builds Docker image)
make migrate     # Apply database migrations
```

**Verify it works:**
- http://localhost:8000 - API health check
- http://localhost:8000/docs - Interactive API docs

### Backend (via Docker)

The backend runs in Docker for environment consistency. Use the Makefile for convenience:

```bash
# Development workflow
make help        # Show all available commands
make up          # Start backend services (with build)
make down        # Stop services
make logs        # View logs (follow mode)
make shell       # Open bash shell in backend container

# Database migrations
make migration msg="describe change"  # Generate new migration
make migrate                          # Apply pending migrations
make db-reset                         # Reset database (destructive!)

# Testing (when implemented)
make test        # Run all tests
```

**Without Make (direct docker compose):**
```bash
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "describe change"
docker compose exec backend pytest
```

### Data Directory

- Backend persistent data: `./backend/data:/app/data`
- Environment variable: `TEVILDO_DATA_DIR=/app/data`
- SQLite database: `backend/data/app.db`
- Invoice PDFs: `backend/data/invoices/`

## Architecture Essentials

### Invoice Lifecycle States

1. `UPLOADED` - PDF received, no parsing yet
2. `PARSED` - Successfully parsed by automated system
3. `NEEDS_REVIEW` - Parsing ambiguous or missing fields, requires manual review

### Data Model Critical Concepts

**Snapshot Philosophy (VERY IMPORTANT):**
- Once an invoice is locked (`locked_at` is set), financial fields are **immutable**
- Exchange rates (`fx_rate`, `fx_date`, `fx_source`) are stored per invoice, never recomputed
- Category versions are versioned by validity period; invoices reference the version active at issue time
- This ensures audit-safe historical reports that never change when regulations or FX rates change

**Database Design Conventions:**
- All IDs are UUID v4 stored as TEXT
- Dates stored as ISO-8601 TEXT: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`
- Booleans stored as INTEGER (0/1) with CHECK constraints
- SQLite foreign keys must be enabled: `PRAGMA foreign_keys = ON`

### Key Services (when implemented)

- `pdf_parser.py` - Extracts structured data from invoice PDFs (best-effort, not authoritative)
- `fx_provider.py` - Resolves official exchange rates by date (deterministic, persisted per invoice)
- `reporting.py` - Generates Excel summaries and ZIP packages for accountants

### Monotributo Logic

- Category tables (`monotributo_category_version`) are **immutable once created**
- New regulatory changes create new versions, never modify existing ones
- Calculations always reference the invoice issue date and the category table valid at that time
- Split into two tables:
  - `monotributo_category_version` - version metadata (name, validity period)
  - `monotributo_category_limit` - actual limits per category within a version

## Database Migrations

**Non-Negotiable Rules:**
1. All schema changes go through Alembic migrations
2. Never edit a committed migration
3. No manual `ALTER TABLE` on user databases
4. Backward compatibility preferred over rewrites
5. Migrations must preserve audit-safety

**SQLite Limitations:**
- No `DROP COLUMN` support
- Limited `ALTER TABLE` capabilities
- When needed: create new table, copy data, drop old, rename new
- Alembic scripts must handle this explicitly

**Workflow:**
1. Modify SQLAlchemy models in `backend/app/models/`
2. Generate: `alembic revision --autogenerate -m "description"`
3. **Manually review** generated operations
4. Apply: `alembic upgrade head`
5. Commit migration file

## Code Structure (when implemented)

```
tevildo/
├── frontend/              # Next.js + shadcn/ui
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI endpoints
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── services/     # Business logic (parsing, FX, reporting)
│   │   └── settings.py   # Configuration
│   ├── data/
│   │   ├── app.db       # SQLite database (gitignored)
│   │   └── invoices/    # Stored PDFs (gitignored)
│   └── main.py          # FastAPI entrypoint
└── alembic/             # Database migrations
```

## Important Guidelines

### Security & Data Integrity
- Never commit files that likely contain secrets (.env, credentials.json, app.db)
- Validate input at system boundaries (user input, external APIs)
- No command injection, XSS, or SQL injection vulnerabilities

### File Storage
- Invoice PDFs stored on filesystem, **not** in database
- `stored_file` table tracks metadata (path, SHA256, MIME type, size)
- Enables integrity checks and deduplication

### Audit Trail
- `invoice_parse_attempt` table logs every parsing attempt
- Never overwrite parsing history
- Enables debugging and explains why invoices were flagged for review

### Simplicity Over Complexity
- This is a local-first, single-user application
- No microservices, no event-driven infrastructure
- No over-engineering: build only what's explicitly needed
- Manual correctness before automation

## Explicit Non-Goals

- ARCA/AFIP integration
- Multi-user support
- Cloud hosting (initially)
- Mobile-first UX
- Automated invoice issuance

## Related Documentation

- `README.md` - Project goals and overview
- `ARCHITECTURE.md` - Design decisions and module structure
- `DATABASE.md` - Concrete schema specification
- `DATA_MODEL.md` - Database design rationale and SQLite tradeoffs
- `MIGRATIONS.md` - Migration strategy and Docker usage
- `ROADMAP.md` - Phase-by-phase implementation plan
