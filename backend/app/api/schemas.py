"""
Pydantic schemas for API request/response models.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator

class InvoiceResponse(BaseModel):
    """Response model for a single invoice."""
    id: str
    status: str
    uploaded_at: datetime
    issue_date: Optional[str] = None
    invoice_type: Optional[str] = None
    invoice_number: Optional[str] = None
    client_name: Optional[str] = None
    client_tax_id: Optional[str] = None
    currency: Optional[str] = None
    total_ars: Optional[float] = None
    total_original: Optional[float] = None
    fx_rate: Optional[float] = None
    fx_date: Optional[str] = None
    fx_source: Optional[str] = None
    notes: Optional[str] = None
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

class InvoiceUpdate(BaseModel):
    """Schema for updating invoice fields."""
    issue_date: Optional[str] = None
    invoice_type: Optional[str] = None
    invoice_number: Optional[str] = None
    client_name: Optional[str] = None
    client_tax_id: Optional[str] = None
    currency: Optional[str] = None
    total_ars: Optional[float] = None
    total_original: Optional[float] = None
    fx_rate: Optional[float] = None
    fx_date: Optional[str] = None
    fx_source: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('issue_date', 'fx_date')
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate dates are in ISO format (YYYY-MM-DD)."""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Date must be in ISO format (YYYY-MM-DD), got: {v}")

    @field_validator('invoice_type')
    @classmethod
    def validate_invoice_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate invoice type is one of the allowed values."""
        if v is None:
            return v
        allowed = ['A', 'B', 'C', 'E', 'M']
        if v not in allowed:
            raise ValueError(f"Invoice type must be one of {allowed}, got: {v}")
        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency is one of the allowed values."""
        if v is None:
            return v
        allowed = ['ARS', 'USD', 'EUR']
        if v not in allowed:
            raise ValueError(f"Currency must be one of {allowed}, got: {v}")
        return v

    @field_validator('total_ars', 'total_original', 'fx_rate')
    @classmethod
    def validate_positive_numbers(cls, v: Optional[float]) -> Optional[float]:
        """Validate numeric fields are positive."""
        if v is None:
            return v
        if v <= 0:
            raise ValueError(f"Value must be positive, got: {v}")
        return v
