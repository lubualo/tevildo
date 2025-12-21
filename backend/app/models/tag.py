"""
Tag models - flexible invoice categorization.
"""
from sqlalchemy import Column, String, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.database import Base


# Join table for many-to-many relationship between Invoice and Tag
# This is NOT a class, it's a Table object used by SQLAlchemy
invoice_tag = Table(
    'invoice_tag',
    Base.metadata,
    Column('invoice_id', String, ForeignKey('invoice.id'), primary_key=True),
    Column('tag_id', String, ForeignKey('tag.id'), primary_key=True)
)


class Tag(Base):
    """
    Simple tagging system for flexible invoice grouping.

    Examples: "client:acme", "project:alpha", "export", "reviewed"
    """
    __tablename__ = "tag"

    # Primary key
    id = Column(String, primary_key=True)  # UUID as TEXT

    # Tag data
    name = Column(String, nullable=False, unique=True)

    # Relationships
    invoices = relationship(
        "Invoice",
        secondary=invoice_tag,  # Use the join table
        back_populates="tags"
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"
