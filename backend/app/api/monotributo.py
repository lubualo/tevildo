"""
Monotributo API endpoints.
"""
from typing import List
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.monotributo import MonotributoCategoryVersion, MonotributoCategoryLimit
from app.models.invoice import Invoice
from app.models.settings import UserSettings
from app.services.arca_scraper import ARCAScraper

router = APIRouter(prefix="/api/monotributo", tags=["monotributo"])


@router.get("/categories/current")
async def get_current_categories(db: Session = Depends(get_db)):
    """
    Get the currently active category version with all limits.

    Returns the most recent version (by valid_from date) where valid_to is NULL.
    Includes all category limits (A-K) for that version.
    """
    # Find the current version (valid_to is NULL, most recent valid_from)
    current_version = (
        db.query(MonotributoCategoryVersion)
        .filter(MonotributoCategoryVersion.valid_to == None)
        .order_by(MonotributoCategoryVersion.valid_from.desc())
        .first()
    )

    if not current_version:
        raise HTTPException(
            status_code=404,
            detail="No active category version found"
        )

    # Get all limits for this version
    limits = (
        db.query(MonotributoCategoryLimit)
        .filter(MonotributoCategoryLimit.version_id == current_version.id)
        .order_by(MonotributoCategoryLimit.category_letter)
        .all()
    )

    # Build response
    return {
        "version": {
            "id": current_version.id,
            "name": current_version.name,
            "valid_from": current_version.valid_from,
            "valid_to": current_version.valid_to,
            "notes": current_version.notes,
        },
        "categories": [
            {
                "category_letter": limit.category_letter,
                "annual_income_limit_services": float(limit.annual_income_limit_services),
                "annual_income_limit_goods": float(limit.annual_income_limit_goods),
                "surface_limit_m2": limit.surface_limit_m2,
                "electricity_limit_kwh": limit.electricity_limit_kwh,
                "annual_rent_limit_ars": float(limit.annual_rent_limit_ars) if limit.annual_rent_limit_ars else None,
                "integrated_tax_services": float(limit.integrated_tax_services) if limit.integrated_tax_services else None,
                "integrated_tax_goods": float(limit.integrated_tax_goods) if limit.integrated_tax_goods else None,
                "pension_contribution_services": float(limit.pension_contribution_services) if limit.pension_contribution_services else None,
                "pension_contribution_goods": float(limit.pension_contribution_goods) if limit.pension_contribution_goods else None,
                "social_security_services": float(limit.social_security_services) if limit.social_security_services else None,
                "social_security_goods": float(limit.social_security_goods) if limit.social_security_goods else None,
                "total_monthly_services": float(limit.total_monthly_services) if limit.total_monthly_services else None,
                "total_monthly_goods": float(limit.total_monthly_goods) if limit.total_monthly_goods else None,
            }
            for limit in limits
        ]
    }


@router.post("/categories/update")
async def update_categories_from_arca(db: Session = Depends(get_db)):
    """
    Update Monotributo categories from ARCA website.

    - Scrapes current data from ARCA
    - Compares with existing current version
    - Creates new version if data has changed
    - Returns status and details about the update
    """
    # Scrape fresh data from ARCA
    scraper = ARCAScraper()
    try:
        scraped_data = scraper.scrape()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape ARCA data: {str(e)}"
        )

    # Get current version from database
    current_version = (
        db.query(MonotributoCategoryVersion)
        .filter(MonotributoCategoryVersion.valid_to == None)
        .order_by(MonotributoCategoryVersion.valid_from.desc())
        .first()
    )

    # If no current version exists, create the first one
    if not current_version:
        version_id = str(uuid.uuid4())
        new_version = MonotributoCategoryVersion(
            id=version_id,
            name="2025-v1",
            valid_from=scraped_data['version_info']['valid_from'],
            valid_to=None,
            notes=scraped_data['version_info']['notes'],
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_version)

        # Add all categories
        for cat_data in scraped_data['categories']:
            limit = MonotributoCategoryLimit(
                id=str(uuid.uuid4()),
                version_id=version_id,
                **cat_data,
                created_at=datetime.now(timezone.utc)
            )
            db.add(limit)

        db.commit()

        return {
            "status": "created",
            "message": "First version created from ARCA data",
            "version_name": new_version.name,
            "categories_count": len(scraped_data['categories'])
        }

    # Get current limits for comparison
    current_limits = (
        db.query(MonotributoCategoryLimit)
        .filter(MonotributoCategoryLimit.version_id == current_version.id)
        .order_by(MonotributoCategoryLimit.category_letter)
        .all()
    )

    # Compare scraped data with current version
    data_changed = _has_data_changed(current_limits, scraped_data['categories'])
    valid_from_changed = current_version.valid_from != scraped_data['version_info']['valid_from']

    # If nothing changed, return early
    if not data_changed and not valid_from_changed:
        return {
            "status": "up_to_date",
            "message": "Categories are already up to date with ARCA",
            "version_name": current_version.name,
            "valid_from": current_version.valid_from
        }

    # Data has changed - create new version
    # First, expire the current version
    from datetime import date
    today = date.today().isoformat()
    current_version.valid_to = today

    # Determine new version name
    # Extract version number from current name (e.g., "2025-v1" -> 1)
    current_name_parts = current_version.name.split('-v')
    if len(current_name_parts) == 2:
        year = current_name_parts[0]
        version_num = int(current_name_parts[1]) + 1
        new_name = f"{year}-v{version_num}"
    else:
        # Fallback if naming convention is different
        new_name = f"2025-v{len(db.query(MonotributoCategoryVersion).all()) + 1}"

    # Create new version
    version_id = str(uuid.uuid4())
    new_version = MonotributoCategoryVersion(
        id=version_id,
        name=new_name,
        valid_from=scraped_data['version_info']['valid_from'],
        valid_to=None,
        notes=scraped_data['version_info']['notes'],
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_version)

    # Add all categories for new version
    for cat_data in scraped_data['categories']:
        limit = MonotributoCategoryLimit(
            id=str(uuid.uuid4()),
            version_id=version_id,
            **cat_data,
            created_at=datetime.now(timezone.utc)
        )
        db.add(limit)

    db.commit()

    return {
        "status": "updated",
        "message": "New version created from ARCA data",
        "old_version": current_version.name,
        "new_version": new_version.name,
        "valid_from": new_version.valid_from,
        "categories_count": len(scraped_data['categories']),
        "changes_detected": data_changed
    }


def _has_data_changed(current_limits: List[MonotributoCategoryLimit], scraped_categories: List[dict]) -> bool:
    """
    Compare current database limits with scraped ARCA data.
    Returns True if any significant differences are found.
    """
    if len(current_limits) != len(scraped_categories):
        return True

    # Create lookup dict for scraped data
    scraped_dict = {cat['category_letter']: cat for cat in scraped_categories}

    for limit in current_limits:
        scraped = scraped_dict.get(limit.category_letter)
        if not scraped:
            return True  # Category missing in scraped data

        # Compare key financial fields
        if (
            limit.annual_income_limit_services != scraped['annual_income_limit_services'] or
            limit.annual_income_limit_goods != scraped['annual_income_limit_goods'] or
            limit.total_monthly_services != scraped['total_monthly_services'] or
            limit.total_monthly_goods != scraped['total_monthly_goods']
        ):
            return True

    return False


@router.get("/usage")
async def get_category_usage(db: Session = Depends(get_db)):
    """
    Calculate rolling 12-month income and usage across all categories.

    Returns:
    - Rolling 12-month total (from locked invoices)
    - Usage percentage and remaining margin for each category
    - Current user settings (company name, selected category, income type)
    - Invoice count
    - Date range
    """
    # Get user settings
    settings = db.query(UserSettings).first()
    if not settings:
        # Create default if doesn't exist
        settings = UserSettings(
            id=str(uuid.uuid4()),
            company_name=None,
            current_category=None,
            income_type="services",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    # Calculate date range (12 months back from today)
    today = date.today()
    twelve_months_ago = today - timedelta(days=365)

    # Query locked invoices from last 12 months
    invoices = db.query(Invoice).filter(
        Invoice.locked_at.isnot(None),
        Invoice.issue_date >= twelve_months_ago.isoformat(),
        Invoice.issue_date <= today.isoformat()
    ).all()

    # Calculate total
    rolling_total = sum(
        float(inv.total_ars) if inv.total_ars else 0
        for inv in invoices
    )

    # Get current category version
    current_version = (
        db.query(MonotributoCategoryVersion)
        .filter(MonotributoCategoryVersion.valid_to == None)
        .order_by(MonotributoCategoryVersion.valid_from.desc())
        .first()
    )

    if not current_version:
        raise HTTPException(
            status_code=404,
            detail="No active category version found. Please update categories from ARCA."
        )

    # Get all category limits
    limits = (
        db.query(MonotributoCategoryLimit)
        .filter(MonotributoCategoryLimit.version_id == current_version.id)
        .order_by(MonotributoCategoryLimit.category_letter)
        .all()
    )

    # Calculate usage for each category
    categories_usage = []
    for limit in limits:
        # Choose limit based on user's income type
        if settings.income_type == "services":
            annual_limit = float(limit.annual_income_limit_services)
        else:
            annual_limit = float(limit.annual_income_limit_goods)

        # Calculate percentage and remaining
        percentage = (rolling_total / annual_limit * 100) if annual_limit > 0 else 0
        remaining = annual_limit - rolling_total

        # Determine status
        if percentage >= 90:
            status = "danger"
        elif percentage >= 70:
            status = "warning"
        else:
            status = "safe"

        categories_usage.append({
            "category_letter": limit.category_letter,
            "limit": annual_limit,
            "used": rolling_total,
            "percentage": round(percentage, 2),
            "remaining": remaining,
            "status": status,
            "is_current": limit.category_letter == settings.current_category
        })

    return {
        "rolling_12mo_total_ars": rolling_total,
        "date_range": {
            "from": twelve_months_ago.isoformat(),
            "to": today.isoformat()
        },
        "invoice_count": len(invoices),
        "current_category": settings.current_category,
        "company_name": settings.company_name,
        "income_type": settings.income_type,
        "categories": categories_usage
    }
