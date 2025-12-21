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
    name = Column(String, nullable=False)  # e.g., "ARCA update Jan 2025"
    valid_from = Column(String, nullable=False)  # ISO-8601: YYYY-MM-DD
    valid_to = Column(String, nullable=True)  # ISO-8601: YYYY-MM-DD, NULL if current

    # Status
    is_active = Column(Integer, nullable=False, default=1)  # Boolean as INTEGER (0/1)

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

    # Category data
    category_code = Column(String, nullable=False)  # A, B, C, D, E, F, G, H, I, J, K
    annual_ars_limit = Column(Numeric(precision=15, scale=2), nullable=False)

    # Relationship
    version = relationship("MonotributoCategoryVersion", back_populates="limits")

    # Constraints
    __table_args__ = (
        UniqueConstraint('version_id', 'category_code', name='uq_version_category'),
    )

    def __repr__(self):
        return f"<MonotributoCategoryLimit(category={self.category_code}, limit={self.annual_ars_limit})>"
