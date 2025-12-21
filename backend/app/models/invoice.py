"""
Invoice models - core business entities.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Invoice(Base):
    """
    Central business entity representing an issued invoice.

    Stores immutable tax snapshot once locked.
    All financial fields (amounts, FX rates) are snapshots, never recomputed.
    """
    __tablename__ = "invoice"

    # Primary key
    id = Column(String, primary_key=True)  # UUID as TEXT

    # Lifecycle
    status = Column(String, nullable=False)  # UPLOADED, PARSED, NEEDS_REVIEW
    uploaded_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    parsed_at = Column(DateTime, nullable=True)
    locked_at = Column(DateTime, nullable=True)  # Once set, data is immutable

    # Invoice identity
    invoice_type = Column(String, nullable=True)  # e.g., "A", "B", "C"
    point_of_sale = Column(String, nullable=True)  # Punto de venta
    invoice_number = Column(String, nullable=True)

    # Dates
    issue_date = Column(String, nullable=True)  # ISO-8601: YYYY-MM-DD

    # Client snapshot (captured at invoice time)
    client_name = Column(String, nullable=True)
    client_tax_id = Column(String, nullable=True)  # CUIT/CUIL

    # Amounts
    currency = Column(String, nullable=True)  # ARS, USD
    total_original = Column(Numeric(precision=12, scale=2), nullable=True)  # Original currency
    total_ars = Column(Numeric(precision=12, scale=2), nullable=True)  # Always in ARS

    # FX snapshot (exchange rate at invoice time)
    fx_rate = Column(Numeric(precision=10, scale=4), nullable=True)
    fx_date = Column(String, nullable=True)  # ISO-8601: YYYY-MM-DD
    fx_source = Column(String, nullable=True)  # e.g., "Banco Central", "Manual"

    # Optional metadata
    notes = Column(Text, nullable=True)

    # Foreign Keys
    stored_file_id = Column(
        String,
        ForeignKey("stored_file.id"),
        nullable=False
    )
    category_version_id = Column(
        String,
        ForeignKey("monotributo_category_version.id"),
        nullable=True
    )

    # Relationships
    stored_file = relationship("StoredFile", back_populates="invoice")
    category_version = relationship("MonotributoCategoryVersion", back_populates="invoices")
    parse_attempts = relationship(
        "InvoiceParseAttempt",
        back_populates="invoice",
        cascade="all, delete-orphan"  # Delete attempts when invoice deleted
    )
    tags = relationship(
        "Tag",
        secondary="invoice_tag",  # Join table
        back_populates="invoices"
    )

    def __repr__(self):
        return f"<Invoice(id={self.id}, status={self.status}, issue_date={self.issue_date})>"


class InvoiceParseAttempt(Base):
    """
    Audit trail of parsing attempts.

    Every parsing attempt is stored (never overwritten) for debugging
    and explainability.
    """
    __tablename__ = "invoice_parse_attempt"

    # Primary key
    id = Column(String, primary_key=True)  # UUID as TEXT

    # Foreign key
    invoice_id = Column(
        String,
        ForeignKey("invoice.id"),
        nullable=False
    )

    # Parsing metadata
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    parser_name = Column(String, nullable=False)  # e.g., "pdfplumber_v1"
    confidence = Column(Numeric(precision=3, scale=2), nullable=True)  # 0.00 to 1.00
    warnings = Column(Text, nullable=True)  # JSON or text warnings
    extracted_json = Column(Text, nullable=True)  # Raw extracted data as JSON

    # Relationship
    invoice = relationship("Invoice", back_populates="parse_attempts")

    def __repr__(self):
        return f"<InvoiceParseAttempt(id={self.id}, parser={self.parser_name}, confidence={self.confidence})>"
