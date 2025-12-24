"""
Invoice API endpoints.
"""
import hashlib
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.settings import settings
from app.models import Invoice, StoredFile, InvoiceParseAttempt
from app.api.schemas import InvoiceResponse, InvoiceListResponse, UploadResponse, FileInfo, InvoiceUpdate
from app.services.pdf_parser import InvoiceParser

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

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a single invoice by ID.

    Returns full invoice details including all fields.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail=f"Invoice {invoice_id} not found"
        )

    return InvoiceResponse.model_validate(invoice)

@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: str,
    db: Session = Depends(get_db)
):
    """
    Serve the PDF file for an invoice.

    Returns the raw PDF file for browser viewing.
    """
    # Get the invoice
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail=f"Invoice {invoice_id} not found"
        )

    # Get the stored file
    stored_file = db.query(StoredFile).filter(StoredFile.id == invoice.stored_file_id).first()

    if not stored_file:
        raise HTTPException(
            status_code=404,
            detail=f"PDF file not found for invoice {invoice_id}"
        )

    # Build the full file path
    file_path = settings.tevildo_data_dir / stored_file.relative_path

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"PDF file does not exist on disk: {stored_file.relative_path}"
        )

    # Return the PDF file
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline"
        }
    )

@router.get("/{invoice_id}/parse-attempts", response_model=list)
async def get_parse_attempts(
    invoice_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all parse attempts for an invoice.

    Returns the parsing history, most recent first.
    """
    attempts = (
        db.query(InvoiceParseAttempt)
        .filter(InvoiceParseAttempt.invoice_id == invoice_id)
        .order_by(InvoiceParseAttempt.created_at.desc())
        .all()
    )

    # Convert to dict for JSON response
    result = []
    for attempt in attempts:
        import json

        # Parse the extracted_json string back to dict
        try:
            extracted_data = eval(attempt.extracted_json) if attempt.extracted_json else {}
        except:
            extracted_data = {}

        result.append({
            "id": attempt.id,
            "created_at": attempt.created_at,
            "parser_name": attempt.parser_name,
            "confidence": attempt.confidence,
            "warnings": attempt.warnings,
            "extracted_data": extracted_data,
        })

    return result

@router.post("/{invoice_id}/lock", response_model=InvoiceResponse)
async def lock_invoice(
    invoice_id: str,
    db: Session = Depends(get_db)
):
    """
    Lock an invoice to make it immutable.

    Once locked, the invoice cannot be updated or deleted.
    This is critical for audit-safety and regulatory compliance.
    """
    # Get the invoice
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail=f"Invoice {invoice_id} not found"
        )

    # Check if already locked
    if invoice.locked_at is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Invoice already locked at: {invoice.locked_at}"
        )

    # Lock the invoice with current timestamp
    invoice.locked_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)

@router.post("/upload", response_model=UploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an invoice PDF.

    Creates a StoredFile record and an Invoice record in UPLOADED state.
    Then parses the PDF to extract invoice data.
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

    # Parse the PDF to extract invoice data
    try:
        parse_start = time.time()
        
        parser = InvoiceParser(file_path)
        parse_result = parser.parse()

        parse_duration = time.time() - parse_start
        print(f"⏱️  PDF parsing took {parse_duration:.3f} seconds for invoice {invoice_id}")
        
        # Create parse attempt record
        parse_attempt = InvoiceParseAttempt(
            id=str(uuid.uuid4()),
            invoice_id=invoice_id,
            parser_name="pdfplumber_v1",
            confidence=parse_result.get("confidence", 0.0),
            warnings=f"Parse time: {parse_duration:.3f}s" if parse_duration > 2.0 else None,  # ← Add timing to warnings if slow
            extracted_json=str(parse_result),  # Store full result as JSON string
        )
        db.add(parse_attempt)

        # Update invoice status based on confidence
        if parse_result.get("success") and parse_result.get("confidence", 0) >= 0.7:
            invoice.status = "PARSED"
            invoice.parsed_at = datetime.now(timezone.utc)
        elif parse_result.get("success"):
            invoice.status = "NEEDS_REVIEW"
            invoice.parsed_at = datetime.now(timezone.utc)
        # else: keep status as "UPLOADED" (parsing failed)

        db.commit()
        db.refresh(invoice)

    except Exception as e:
        # If parsing fails, don't block the upload
        # Just log the error and keep invoice as UPLOADED
        print(f"Warning: Failed to parse invoice {invoice_id}: {e}")
        # Could save error to parse_attempt table here

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

@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    update_data: InvoiceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update invoice fields.

    Only unlocked invoices can be updated.
    Only provided fields are updated (partial update).
    """
    # Get the invoice
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail=f"Invoice {invoice_id} not found"
        )

    # Check if locked
    if invoice.locked_at is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update locked invoice. Locked at: {invoice.locked_at}"
        )

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)

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
