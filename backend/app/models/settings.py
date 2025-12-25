"""
User settings model.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, CheckConstraint
from app.database import Base


class UserSettings(Base):
    """
    User settings for the application.

    Single-user application, so this table should only have one row.
    Contains preferences like company name, current Monotributo category, etc.
    """
    __tablename__ = "user_settings"

    id = Column(String, primary_key=True)

    # Company/user information
    company_name = Column(String, nullable=True)

    # Monotributo preferences
    current_category = Column(
        String,
        nullable=True,
        # Validate category is A-K
    )
    income_type = Column(
        String,
        nullable=False,
        default="services",
        # Validate income_type is services or goods
    )

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "current_category IS NULL OR current_category IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K')",
            name="valid_category"
        ),
        CheckConstraint(
            "income_type IN ('services', 'goods')",
            name="valid_income_type"
        ),
    )
