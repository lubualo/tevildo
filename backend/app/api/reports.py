"""
Reports API endpoints.

Generates downloadable reports for accountants.
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.invoice import Invoice
from app.models.stored_file import StoredFile
from app.models.settings import UserSettings
from app.models.monotributo import MonotributoCategoryVersion, MonotributoCategoryLimit
from app.services.excel_report import ExcelReportGenerator
from app.services.zip_export import ZipExportGenerator
from app.settings import settings as app_settings

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/excel")
async def export_excel_report(db: Session = Depends(get_db)):
    """
    Generate and download Excel report with invoice summary.

    Includes:
    - Summary sheet with totals and category usage
    - Detailed invoices list
    - Monthly breakdown with cumulative totals
    """
    # Get user settings
    settings = db.query(UserSettings).first()
    if not settings:
        import uuid
        from datetime import datetime, timezone
        settings = UserSettings(
            id=str(uuid.uuid4()),
            company_name=None,
            current_category=None,
            income_type="services",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    # Calculate date range (rolling 12 months)
    date_to = date.today()
    date_from = date_to - timedelta(days=365)

    # Get locked invoices in period
    invoices = db.query(Invoice).filter(
        Invoice.locked_at.isnot(None),
        Invoice.issue_date >= date_from.isoformat(),
        Invoice.issue_date <= date_to.isoformat()
    ).order_by(Invoice.issue_date.desc()).all()

    # Get category info if user has selected one
    category_info = None
    if settings.current_category:
        current_version = (
            db.query(MonotributoCategoryVersion)
            .filter(MonotributoCategoryVersion.valid_to == None)
            .order_by(MonotributoCategoryVersion.valid_from.desc())
            .first()
        )

        if current_version:
            limit = (
                db.query(MonotributoCategoryLimit)
                .filter(
                    MonotributoCategoryLimit.version_id == current_version.id,
                    MonotributoCategoryLimit.category_letter == settings.current_category
                )
                .first()
            )

            if limit:
                if settings.income_type == "services":
                    annual_limit = float(limit.annual_income_limit_services)
                else:
                    annual_limit = float(limit.annual_income_limit_goods)

                total_ars = sum(float(inv.total_ars or 0) for inv in invoices)
                percentage = (total_ars / annual_limit * 100) if annual_limit > 0 else 0

                category_info = {
                    "limit": annual_limit,
                    "percentage": percentage,
                    "remaining": annual_limit - total_ars,
                }

    # Generate report
    generator = ExcelReportGenerator(
        invoices=invoices,
        settings=settings,
        date_from=date_from,
        date_to=date_to,
        category_info=category_info,
    )
    excel_file = generator.generate()

    # Generate filename
    company_slug = (settings.company_name or "tevildo").lower().replace(" ", "-")
    filename = f"{company_slug}-monotributo-{date_to.strftime('%Y-%m')}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/zip")
async def export_zip_with_pdfs(db: Session = Depends(get_db)):
    """
    Generate ZIP archive with invoice PDFs grouped by month.

    Includes:
    - PDFs organized in YYYY-MM folders
    - Excel summary report
    - README with export details
    """
    # Get user settings
    user_settings = db.query(UserSettings).first()
    if not user_settings:
        import uuid
        from datetime import datetime, timezone
        user_settings = UserSettings(
            id=str(uuid.uuid4()),
            company_name=None,
            current_category=None,
            income_type="services",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    # Calculate date range (rolling 12 months)
    date_to = date.today()
    date_from = date_to - timedelta(days=365)

    # Get locked invoices in period
    invoices = db.query(Invoice).filter(
        Invoice.locked_at.isnot(None),
        Invoice.issue_date >= date_from.isoformat(),
        Invoice.issue_date <= date_to.isoformat()
    ).order_by(Invoice.issue_date.desc()).all()

    # Get stored files for these invoices
    stored_files = {}
    for inv in invoices:
        sf = db.query(StoredFile).filter(StoredFile.id == inv.stored_file_id).first()
        if sf:
            stored_files[inv.id] = sf

    # Get category info if available
    category_info = _get_category_info(db, user_settings, invoices)

    # Generate ZIP
    generator = ZipExportGenerator(
        invoices=invoices,
        stored_files=stored_files,
        user_settings=user_settings,
        date_from=date_from,
        date_to=date_to,
        category_info=category_info,
    )
    zip_file = generator.generate()

    # Generate filename
    company_slug = (user_settings.company_name or "tevildo").lower().replace(" ", "-")
    filename = f"{company_slug}-invoices-{date_to.strftime('%Y-%m')}.zip"

    return StreamingResponse(
        zip_file,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/backup")
async def export_full_backup(db: Session = Depends(get_db)):
    """
    Generate complete backup ZIP with ALL data.

    Includes:
    - All invoice PDFs (not just locked, not filtered by date)
    - Excel report with all invoices
    - Database export info
    - README with backup details
    """
    import json
    import zipfile
    from io import BytesIO

    # Get ALL invoices (not filtered)
    all_invoices = db.query(Invoice).order_by(Invoice.issue_date.desc()).all()

    # Get user settings
    user_settings = db.query(UserSettings).first()

    # Get all stored files
    stored_files = {}
    for inv in all_invoices:
        sf = db.query(StoredFile).filter(StoredFile.id == inv.stored_file_id).first()
        if sf:
            stored_files[inv.id] = sf

    output = BytesIO()

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add all PDFs
        for inv in all_invoices:
            stored_file = stored_files.get(inv.id)
            if not stored_file:
                continue

            file_path = app_settings.tevildo_data_dir / stored_file.relative_path
            if not file_path.exists():
                continue

            # Organize by status and date
            status = inv.status or "unknown"
            issue_date = inv.issue_date or "no-date"
            invoice_num = (inv.invoice_number or "unknown").replace("/", "-")

            arcname = f"pdfs/{status}/{issue_date}_{invoice_num}.pdf"
            zf.write(file_path, arcname)

        # Add invoice data as JSON
        invoices_data = []
        for inv in all_invoices:
            invoices_data.append({
                "id": inv.id,
                "status": inv.status,
                "invoice_type": inv.invoice_type,
                "invoice_number": inv.invoice_number,
                "issue_date": inv.issue_date,
                "client_name": inv.client_name,
                "client_tax_id": inv.client_tax_id,
                "currency": inv.currency,
                "total_original": float(inv.total_original) if inv.total_original else None,
                "total_ars": float(inv.total_ars) if inv.total_ars else None,
                "fx_rate": float(inv.fx_rate) if inv.fx_rate else None,
                "fx_date": inv.fx_date,
                "locked_at": inv.locked_at.isoformat() if inv.locked_at else None,
                "uploaded_at": inv.uploaded_at.isoformat() if inv.uploaded_at else None,
            })
        zf.writestr("data/invoices.json", json.dumps(invoices_data, indent=2))

        # Add settings as JSON
        if user_settings:
            settings_data = {
                "company_name": user_settings.company_name,
                "current_category": user_settings.current_category,
                "income_type": user_settings.income_type,
            }
            zf.writestr("data/settings.json", json.dumps(settings_data, indent=2))

        # Add README
        readme = f"""Tevildo Full Backup
===================

Backup Date: {date.today().strftime('%Y-%m-%d')}
Total Invoices: {len(all_invoices)}
Locked Invoices: {len([i for i in all_invoices if i.locked_at])}

Contents:
- pdfs/ - All invoice PDFs organized by status
- data/invoices.json - Invoice data export
- data/settings.json - User settings

To restore: Import the JSON files and copy PDFs to the data directory.
"""
        zf.writestr("README.txt", readme)

    output.seek(0)

    # Generate filename
    company_slug = (user_settings.company_name if user_settings else "tevildo").lower().replace(" ", "-")
    filename = f"{company_slug}-backup-{date.today().strftime('%Y-%m-%d')}.zip"

    return StreamingResponse(
        output,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _get_category_info(db: Session, settings: UserSettings, invoices: list) -> dict:
    """Helper to get category usage info."""
    if not settings.current_category:
        return None

    current_version = (
        db.query(MonotributoCategoryVersion)
        .filter(MonotributoCategoryVersion.valid_to == None)
        .order_by(MonotributoCategoryVersion.valid_from.desc())
        .first()
    )

    if not current_version:
        return None

    limit = (
        db.query(MonotributoCategoryLimit)
        .filter(
            MonotributoCategoryLimit.version_id == current_version.id,
            MonotributoCategoryLimit.category_letter == settings.current_category
        )
        .first()
    )

    if not limit:
        return None

    if settings.income_type == "services":
        annual_limit = float(limit.annual_income_limit_services)
    else:
        annual_limit = float(limit.annual_income_limit_goods)

    total_ars = sum(float(inv.total_ars or 0) for inv in invoices)
    percentage = (total_ars / annual_limit * 100) if annual_limit > 0 else 0

    return {
        "limit": annual_limit,
        "percentage": percentage,
        "remaining": annual_limit - total_ars,
    }
