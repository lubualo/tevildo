# 🏗️ Tevildo – Architecture & Design Decisions

This document explains the architectural decisions behind **Tevildo** and serves as a reference for contributors or AI agents working on the codebase.

---

## 🧠 Design Principles

1. **Local-first**
   - All data lives on the user's machine
   - No mandatory internet or cloud services

2. **Auditability over automation**
   - Every invoice preserves the exact exchange rate used
   - Historical data must remain immutable and explainable

3. **Low operational complexity**
   - No infrastructure management
   - Minimal dependencies
   - Easy backups

4. **UI-driven workflow**
   - All corrections and validations happen in the custom UI
   - No reliance on framework admin panels

---

## 🧱 Architectural Style

- Modular monolith
- Clear separation of concerns:
  - API layer
  - Domain models
  - Processing services
- Prepared for async/background processing if needed

---

## 🧩 Key Modules

### API Layer
- CRUD for invoices
- Category/version management
- Report and export endpoints

### Services
- `pdf_parser.py`
  - Extracts structured data from invoice PDFs
  - Best-effort parsing with manual correction fallback

- `fx_provider.py`
  - Resolves official exchange rates by date
  - Returns deterministic values to be persisted per invoice

- `reporting.py`
  - Generates Excel summaries
  - Builds ZIP packages for accountants and backups

---

## 🗄️ Persistence Strategy

### Database
- SQLite
- Chosen for:
  - Simplicity
  - Zero infrastructure
  - Single-user concurrency model

### Filesystem
- Invoice PDFs stored outside the DB
- Referenced by path/hash
- Organized by year/month

---

## 🔄 Invoice Processing Flow

1. User uploads PDF
2. Invoice record created (`UPLOADED`)
3. PDF parsing executed
4. If successful → `PARSED`
5. If ambiguous/missing fields → `NEEDS_REVIEW`
6. User confirms or edits extracted data
7. Invoice locked for reporting

---

## 📈 Monotributo Logic

- Category tables are immutable once created
- New regulatory changes are represented as new versions
- Calculations always reference:
  - invoice issue date
  - category table valid at that time

---

## 🚀 Future Extensions (Non-Blocking)

- Background workers for heavy OCR
- Optional cloud sync
- Advanced projections and simulations
- Multi-currency support beyond USD

---

## ❌ Explicitly Avoided

- Microservices
- Event-driven infrastructure
- Direct tax authority integrations
- Over-automation of fiscal decisions

---

## ✅ Summary

Tevildo prioritizes correctness, clarity, and durability over scale.

It is intentionally small, explicit, and controllable — a tool that helps its owner think clearly about their numbers, not hide them.

