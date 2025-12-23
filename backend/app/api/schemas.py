"""
Pydantic schemas for API request/response models.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class InvoiceResponse(BaseModel):
    """Response model for a single invoice."""
    id: str
    status: str
    uploaded_at: datetime
    issue_date: Optional[str] = None
    invoice_type: Optional[str] = None
    invoice_number: Optional[str] = None
    client_name: Optional[str] = None
    currency: Optional[str] = None
    total_ars: Optional[float] = None
    locked_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allows conversion from ORM models


class InvoiceListResponse(BaseModel):
    """Response model for invoice list endpoint."""
    invoices: List[InvoiceResponse]
    total: int
    skip: int
    limit: int

class FileInfo(BaseModel):
    """File information in upload response."""
    id: str
    path: str
    size: int
    sha256: str


class UploadResponse(BaseModel):
    """Response model for upload endpoint."""
    id: str
    status: str
    uploaded_at: datetime
    file: FileInfo
