"""
Invoice API endpoints.
"""
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.settings import settings
from app.models import Invoice, StoredFile
from app.api.schemas import InvoiceResponse, InvoiceListResponse, UploadResponse, FileInfo

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all invoices with pagination.

    Returns invoices ordered by upload date (newest first).
    """
    invoices = (
        db.query(Invoice)
        .order_by(Invoice.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return InvoiceListResponse(
        invoices=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total=db.query(Invoice).count(),
        skip=skip,
        limit=limit,
    )



@router.post("/upload", response_model=UploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an invoice PDF.

    Creates a StoredFile record and an Invoice record in UPLOADED state.
    """
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {max_size / 1024 / 1024}MB"
        )

    # Generate UUIDs
    file_id = str(uuid.uuid4())
    invoice_id = str(uuid.uuid4())

    # Calculate SHA256 hash
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Determine storage path (organized by upload date)
    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    month = now.strftime("%m")

    # Create directory structure
    upload_dir = settings.invoices_dir / year / month
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file with UUID name
    file_extension = ".pdf"
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # Relative path for database (relative to data dir)
    relative_path = f"invoices/{year}/{month}/{filename}"

    # Create StoredFile record
    stored_file = StoredFile(
        id=file_id,
        relative_path=relative_path,
        sha256=sha256_hash,
        mime_type=file.content_type,
        byte_size=file_size,
    )
    db.add(stored_file)

    # Create Invoice record
    invoice = Invoice(
        id=invoice_id,
        status="UPLOADED",
        stored_file_id=file_id,
    )
    db.add(invoice)

    # Commit to database
    db.commit()
    db.refresh(invoice)

    return UploadResponse(
        id=invoice.id,
        status=invoice.status,
        uploaded_at=invoice.uploaded_at,
        file=FileInfo(
            id=stored_file.id,
            path=relative_path,
            size=file_size,
            sha256=sha256_hash,
        )
    )

@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete an invoice and its associated stored file.

    Cascade deletes related records (parse attempts, tags).
    Physical file is also removed from disk.
    """
    # Find the invoice
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail=f"Invoice {invoice_id} not found"
        )

    # Get the stored file before deleting
    stored_file = db.query(StoredFile).filter(StoredFile.id == invoice.stored_file_id).first()

    if stored_file:
        # Delete physical file from disk
        file_path = settings.tevildo_data_dir / stored_file.relative_path
        if file_path.exists():
            file_path.unlink()

    # Delete invoice (cascades to invoice_parse_attempt and invoice_tag due to FK constraints)
    db.delete(invoice)

    # Delete stored_file record
    if stored_file:
        db.delete(stored_file)

    db.commit()

    return {"message": f"Invoice {invoice_id} deleted successfully"}
