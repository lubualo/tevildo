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
from app.models.settings import UserSettings
from app.models.monotributo import MonotributoCategoryVersion, MonotributoCategoryLimit
from app.services.excel_report import ExcelReportGenerator

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
