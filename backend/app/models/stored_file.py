"""
StoredFile model - metadata for files stored on disk.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class StoredFile(Base):
    """
    Metadata for files stored on disk (PDFs).

    Files are NOT stored in the database, only metadata.
    Actual files live in the filesystem at relative_path.
    """
    __tablename__ = "stored_file"

    # Primary key
    id = Column(String, primary_key=True)  # UUID as TEXT

    # File metadata
    relative_path = Column(String, nullable=False, unique=True)
    sha256 = Column(String, nullable=False)  # File hash for integrity
    mime_type = Column(String, nullable=False)  # e.g., "application/pdf"
    byte_size = Column(Integer, nullable=False)

    # Timestamps (always UTC)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    # One-to-one with Invoice (one file per invoice)
    invoice = relationship("Invoice", back_populates="stored_file", uselist=False)

    def __repr__(self):
        return f"<StoredFile(id={self.id}, path={self.relative_path})>"
