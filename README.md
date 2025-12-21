# 🐱 Tevildo

**Tevildo** is a local-first personal application designed to track invoicing and income for Argentine *Monotributo* taxpayers.

It helps prevent category overruns by keeping a precise, auditable record of invoices, exchange rates, and accumulated income, while generating clean reports for accountants.

> Tevildo is **not** integrated with ARCA/AFIP.  
> It is intended for **single-user, personal use**, running locally.

---

## 🎯 Goals

- Store issued invoices (PDFs)
- Automatically parse key data from invoices
- Track annual / rolling 12-month income
- Monitor Monotributo category limits
- Persist exchange rate **per invoice**
- Generate Excel + ZIP reports for accountants
- Reduce manual errors and spreadsheet maintenance

---

## 🧱 Tech Stack

### Frontend
- **Next.js** (App Router)
- **shadcn/ui**
- Desktop-first UI, responsive by default

### Backend
- **FastAPI (Python)**
- Local REST API

### Persistence
- **SQLite** (local database)
- Filesystem storage for invoice PDFs

### Processing
- PDF parsing: `pdfplumber`, `pypdf`
- OCR (optional fallback): Tesseract
- Excel generation: `openpyxl`
- ZIP exports: standard Python libs

---

## 🏗️ Architecture Overview

- Local-first **monolithic but modular** architecture
- No microservices
- No cloud dependency
- Parsing initially synchronous (can be moved to background tasks if needed)

Invoice lifecycle states:
- `UPLOADED`
- `PARSED`
- `NEEDS_REVIEW`

---

## 🧾 Core Concepts

### Invoice
Each invoice persists:
- Issue date
- Invoice type, point of sale, number
- Client data (if available)
- Currency (ARS / USD)
- Total amount (original currency)
- **Exchange rate used**
  - `fx_rate`
  - `fx_date`
  - `fx_source`
- Calculated total in ARS
- Tags / notes
- Original PDF file

**Key rule:**  
> Exchange rates are always stored per invoice to ensure long-term auditability.

---

## 📈 Monotributo Tracking

- Category tables are **versioned by validity period**
- Each version includes:
  - Category name
  - Annual ARS limit
  - Validity dates
- Invoices reference the category table version active at issue time

Computed metrics:
- Annual / rolling 12-month total
- Category usage percentage
- Remaining margin
- Visual traffic-light status

---

## 📊 Reports & Exports

- Excel summary report
  - Totals
  - Invoice detail
  - Monthly pivots
- Accountant package
  - Excel + ZIP with PDFs grouped by month
- Full local backup export
  - SQLite DB + invoice files

---

## 🚫 Explicit Non-Goals

- No ARCA / AFIP integration
- No multi-user support
- No cloud hosting (initially)
- No mobile-first UX
- No automated invoice issuance

---

## 🚀 Getting Started

### Prerequisites

- **Docker** and **Docker Compose** installed
- **Make** (optional, but recommended for easier commands)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tevildo
   ```

2. **Start the backend**
   ```bash
   # With Make (recommended)
   make up

   # Or with docker compose directly
   docker compose up --build
   ```

3. **Run database migrations**
   ```bash
   # In a new terminal
   make migrate

   # Or with docker compose
   docker compose exec backend alembic upgrade head
   ```

4. **Verify it's working**
   - Open http://localhost:8000 - should see API status
   - Open http://localhost:8000/docs - FastAPI interactive docs

### Common Commands

See all available commands:
```bash
make help
```

Key commands:
- `make up` - Start services
- `make down` - Stop services
- `make logs` - View logs
- `make shell` - Open shell in backend container
- `make migration msg="description"` - Create new migration
- `make migrate` - Apply pending migrations

### Project Status

**Phase 0 (Foundations):** ✅ Complete
**Phase 1 (Invoice Ingestion):** 🚧 Not started

See [ROADMAP.md](ROADMAP.md) for detailed progress.

---

## 🗂️ Repository Structure

```yaml
tevildo/
├── frontend/ # Next.js + shadcn
├── backend/
│ ├── app/
│ │ ├── api/ # FastAPI endpoints
│ │ ├── models/ # ORM models
│ │ ├── services/ # parsing, FX, reporting
│ │ └── settings.py
│ ├── data/
│ │ ├── app.db # SQLite database
│ │ └── invoices/ # Stored PDFs
│ └── main.py # FastAPI entrypoint
└── README.md
```
