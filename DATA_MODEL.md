# Tevildo – Data Model & Database Design

This document explains the **data model decisions**, **SQLite-specific tradeoffs**, and **auditability principles** behind Tevildo’s database.

It is meant to be shared with:
- future contributors
- AI agents
- your future self (when asking “why did I do it this way?”)

---

## 1. What is a MIME type?

A **MIME type** (Multipurpose Internet Mail Extensions) is a standardized string that describes the type of a file or payload.

Examples:
- `application/pdf` → PDF document
- `image/png` → PNG image
- `text/plain` → plain text
- `application/json` → JSON data

### Why we store it
In Tevildo, files (invoices) are stored **on disk**, not inside the database. We store the MIME type so that:
- the UI knows how to display or handle the file
- the app doesn’t rely on file extensions (which can be wrong)
- future exports or integrations know what the content actually is

---

## 2. Dates as TEXT instead of DATE

### SQLite reality check
SQLite **does not have a real DATE or TIMESTAMP type**.

It only supports these storage classes:
- `NULL`
- `INTEGER`
- `REAL`
- `TEXT`
- `BLOB`

Keywords like `DATE`, `DATETIME`, or `BOOLEAN` are **type affinities**, not true types with validation.

### Our choice: ISO-8601 TEXT
We store dates and timestamps as **ISO-8601 strings in TEXT columns**:

- Dates: `YYYY-MM-DD`
- Timestamps: `YYYY-MM-DDTHH:MM:SSZ`

Example:
```text
2025-12-20
2025-12-20T14:30:00Z
```

### Why this is good
- Human-readable (great for debugging)
- Sorts correctly as strings
- Portable to Postgres/MySQL later
- Works cleanly with SQL functions

Validation is enforced via:
- application code
- `CHECK` constraints where appropriate

---

## 3. IDs as UUIDs

SQLite has **no native UUID/GUID type**.

### Options
- `TEXT` UUID (e.g. `550e8400-e29b-41d4-a716-446655440000`)
- `BLOB(16)` UUID (compact but annoying to debug)

### Our choice
We use **UUID v4 stored as TEXT**:
- easy to read
- easy to generate (`uuid4()`)
- no central ID coordination

Every table uses:
```sql
id TEXT PRIMARY KEY
```

with the convention:
> All IDs are UUID strings

---

## 4. Booleans as INTEGER

SQLite does not have a real `BOOLEAN` type.

### Convention
- `0` → false
- `1` → true

We store booleans as:
```sql
INTEGER NOT NULL DEFAULT 0
CHECK (column IN (0,1))
```

ORMs (SQLAlchemy) will map this cleanly to `bool` in Python.

---

## 5. Why two Monotributo tables?

We split Monotributo data into **versions** and **limits** for correctness and auditability.

### `monotributo_category_version`
Represents a **published regulation/table version**.

It answers:
- Which official table is this?
- When does it apply?

Example:
- `id = uuid-123`
- `name = "2025-v1"`
- `valid_from = 2025-08-01`
- `valid_to = NULL`
- `notes = "Vigente desde 1/08/2025 (ARCA)"`

This is **metadata**.

---

### `monotributo_category_limit`
Represents the **actual category limits inside a version**.

It answers:
- What is the annual ARS limit for category A, B, C… in this version?
- What are the monthly payment amounts for services vs goods?

Example rows (simplified):
- `(uuid-123, 'A', services: 8_992_597.87, goods: 8_992_597.87, ...)`
- `(uuid-123, 'B', services: 13_175_201.52, goods: 13_175_201.52, ...)`

This avoids:
- duplicating validity dates per category
- accidental inconsistencies

**Note:** Stores both "Locaciones y prestaciones de servicios" (services) and "Venta de cosas muebles" (goods) limits, plus all other ARCA fields for completeness.

---

## 6. Snapshot philosophy (very important)

Tevildo is designed to be **audit-safe**.

That means:

### Invoices are snapshots
Once an invoice is **locked**:
- amounts do not change
- FX rate does not change
- category tables do not retroactively affect it

This is why invoices store:
- `total_ars`
- `fx_rate`, `fx_date`, `fx_source`
- `category_version_id`

Even if regulations or FX providers change later, **historic reports remain correct**.

---

## 7. Audit trail for parsing

### `invoice_parse_attempt`
Every parsing attempt is stored instead of overwritten.

This allows:
- debugging bad parses
- explaining *why* something was flagged for review
- future parser improvements

Typical stored data:
- parser name
- confidence score
- warnings
- raw extracted JSON

This aligns with a **human-in-the-loop** workflow:
> automation assists, humans confirm

---

## 8. Migrations (industry-style)

Even though Tevildo is local-first and uses SQLite, **migrations are mandatory**.

### Why
- schema evolution without breaking user data
- reproducible environments
- safer upgrades

### Tooling choice
- **SQLAlchemy** for models
- **Alembic** for migrations

Approach:
- autogenerate migrations for speed
- review/edit before committing

This gives us the best of both worlds:
- productivity
- correctness

---

## 9. Design principles summary

- SQLite-friendly, not SQLite-naïve
- Auditability > convenience
- Snapshots over recomputation
- Human-readable data where possible
- Industry-grade migrations

Tevildo’s DB is intentionally **boring, explicit, and conservative** — exactly what you want for tax-related data.

