"""
User settings API endpoints.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings import UserSettings

router = APIRouter(prefix="/api/settings", tags=["settings"])


# Pydantic schemas
class SettingsResponse(BaseModel):
    """User settings response schema."""
    id: str
    company_name: Optional[str] = None
    current_category: Optional[str] = None
    income_type: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    """User settings update schema."""
    company_name: Optional[str] = Field(None, max_length=255)
    current_category: Optional[str] = Field(None, pattern="^[A-K]$")
    income_type: Optional[str] = Field(None, pattern="^(services|goods)$")


@router.get("", response_model=SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """
    Get user settings.

    Single-user app, so this returns the one settings row.
    If no settings exist, creates default settings.
    """
    settings = db.query(UserSettings).first()

    if not settings:
        # Create default settings
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

    return SettingsResponse(
        id=settings.id,
        company_name=settings.company_name,
        current_category=settings.current_category,
        income_type=settings.income_type,
        created_at=settings.created_at.isoformat(),
        updated_at=settings.updated_at.isoformat()
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(
    update_data: SettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user settings.

    Only updates fields that are provided (partial update).
    """
    settings = db.query(UserSettings).first()

    if not settings:
        # Create if doesn't exist
        settings = UserSettings(
            id=str(uuid.uuid4()),
            company_name=update_data.company_name,
            current_category=update_data.current_category,
            income_type=update_data.income_type or "services",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(settings)
    else:
        # Update existing
        if update_data.company_name is not None:
            settings.company_name = update_data.company_name
        if update_data.current_category is not None:
            settings.current_category = update_data.current_category
        if update_data.income_type is not None:
            settings.income_type = update_data.income_type

        settings.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(settings)

    return SettingsResponse(
        id=settings.id,
        company_name=settings.company_name,
        current_category=settings.current_category,
        income_type=settings.income_type,
        created_at=settings.created_at.isoformat(),
        updated_at=settings.updated_at.isoformat()
    )
