"""
Monotributo category models - versioned tax category tables.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class MonotributoCategoryVersion(Base):
    """
    Represents a published Monotributo regulation/table version.

    Immutable once created - new regulations create new versions.
    This ensures historical invoices always reference the correct limits.
    """
    __tablename__ = "monotributo_category_version"

    # Primary key
    id = Column(String, primary_key=True)  # UUID as TEXT

    # Version metadata
    name = Column(String, nullable=False)  # e.g., "2025-v1", "2025-v2"
    valid_from = Column(String, nullable=False)  # ISO-8601: YYYY-MM-DD (when this version becomes active)
    valid_to = Column(String, nullable=True)  # ISO-8601: YYYY-MM-DD, NULL if current
    notes = Column(String, nullable=True)  # Optional notes about regulatory changes

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    limits = relationship(
        "MonotributoCategoryLimit",
        back_populates="version",
        cascade="all, delete-orphan"
    )
    invoices = relationship("Invoice", back_populates="category_version")

    def __repr__(self):
        return f"<MonotributoCategoryVersion(id={self.id}, name={self.name}, valid_from={self.valid_from})>"


class MonotributoCategoryLimit(Base):
    """
    Represents category limits within a given Monotributo version.

    Each version has multiple categories (A, B, C, etc.) with their limits.
    Stores all ARCA fields even though we primarily use annual_income_limit_services.
    """
    __tablename__ = "monotributo_category_limit"

    # Primary key
    id = Column(String, primary_key=True)  # UUID as TEXT

    # Foreign key
    version_id = Column(
        String,
        ForeignKey("monotributo_category_version.id"),
        nullable=False
    )

    # Category identifier
    category_letter = Column(String, nullable=False)  # A, B, C, D, E, F, G, H, I, J, K

    # Income limits (the most important fields for our use case)
    annual_income_limit_services = Column(Numeric(precision=15, scale=2), nullable=False)  # Locaciones y prestaciones
    annual_income_limit_goods = Column(Numeric(precision=15, scale=2), nullable=False)     # Venta de cosas muebles

    # Physical/consumption limits
    surface_limit_m2 = Column(Integer, nullable=True)           # Superficie afectada (m²)
    electricity_limit_kwh = Column(Integer, nullable=True)      # Energía eléctrica consumida (kWh)
    annual_rent_limit_ars = Column(Numeric(precision=15, scale=2), nullable=True)  # Alquileres devengados

    # Monthly payment amounts (for reference/future features)
    # Services column
    integrated_tax_services = Column(Numeric(precision=15, scale=2), nullable=True)
    pension_contribution_services = Column(Numeric(precision=15, scale=2), nullable=True)
    social_security_services = Column(Numeric(precision=15, scale=2), nullable=True)

    # Goods column
    integrated_tax_goods = Column(Numeric(precision=15, scale=2), nullable=True)
    pension_contribution_goods = Column(Numeric(precision=15, scale=2), nullable=True)
    social_security_goods = Column(Numeric(precision=15, scale=2), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    version = relationship("MonotributoCategoryVersion", back_populates="limits")

    # Constraints
    __table_args__ = (
        UniqueConstraint('version_id', 'category_letter', name='uq_version_category'),
    )

    def __repr__(self):
        return f"<MonotributoCategoryLimit(category={self.category_letter}, services_limit={self.annual_income_limit_services})>"
