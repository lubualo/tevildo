# 🧬 Tevildo – Database Migrations Strategy

This document defines **how schema changes are made safely** in Tevildo.

Even though the app is local-first and single-user, migrations are mandatory.

---

## Tooling

- **SQLAlchemy** – ORM & metadata
- **Alembic** – schema migrations
- **SQLite** – execution target
- **Docker** – the standard way to run the backend consistently

---

## Core Rules (Non-Negotiable)

1. **All schema changes go through migrations**
2. **Never edit a committed migration**
3. **No manual `ALTER TABLE` on user databases**
4. **Backward compatibility is preferred over rewrites**
5. Migrations must keep Tevildo **audit-safe**

---

## Migration Workflow

1. Modify SQLAlchemy models
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "describe change"
   ```
3. Review generated operations **manually**
4. Fix unsafe operations (SQLite limitations)
5. Apply locally:
   ```bash
   alembic upgrade head
   ```
6. Commit migration file

---

## Running Alembic with Docker (Recommended)

Tevildo runs the backend in Docker; migrations should be run the same way.

Typical approaches:

### Option A: `docker compose exec` (most common)
```bash
docker compose exec backend alembic upgrade head
```

### Option B: one-off container
```bash
docker compose run --rm backend alembic upgrade head
```

### Environment consistency
- The container should set:
  - `TEVILDO_DATA_DIR=/app/data`
- The compose file should bind-mount:
  - `./backend/data:/app/data`
so Alembic and the app point at the **same SQLite file**.

---

## Naming Conventions

- One logical change per migration
- Message format:
  - `add_invoice_parse_attempt`
  - `add_fx_snapshot_fields`

Migration files are immutable history.

---

## SQLite-Specific Guidelines

SQLite limitations require care:

- No `DROP COLUMN`
- Limited `ALTER TABLE`

**Strategy when needed:**
- Create new table
- Copy data
- Drop old table
- Rename new table

Alembic scripts must handle this explicitly.

---

## Data Safety Principles

- Migrations must be **data-preserving by default**
- Destructive changes require:
  - explicit comment
  - migration doc note
  - ideally a safe fallback path

---

## Version Control

- Migrations live in the repository
- The database schema is **code, not data**
- A fresh clone must reach the same schema via migrations

---

## Downgrades

- Downgrades are supported **only when safe**
- If data loss is unavoidable, downgrade should:
  - raise an exception, or
  - be explicitly documented

---

## Philosophy

Migrations exist to protect:
- historical invoices
- auditability
- your future self

A broken migration is worse than no feature.

When in doubt: **add a new column, don’t rewrite history**.
