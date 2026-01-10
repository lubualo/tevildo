"""
Application startup initialization service.

Handles first-run setup like fetching ARCA categories.
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy.orm import Session

from app.models.monotributo import MonotributoCategoryVersion, MonotributoCategoryLimit
from app.services.arca_scraper import ARCAScraper


def initialize_categories_if_empty(db: Session) -> bool:
    """
    Fetch ARCA categories if no category versions exist.

    This is called on app startup to ensure the database has
    initial category data for first-time users.

    Returns:
        bool: True if categories were fetched, False if already existed
    """
    # Check if any category version exists
    existing_version = db.query(MonotributoCategoryVersion).first()

    if existing_version:
        print("✅ Categories already exist, skipping ARCA fetch")
        return False

    print("📥 No categories found, fetching from ARCA...")

    try:
        scraper = ARCAScraper()
        scraped_data = scraper.scrape()

        # Create first version
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

        print(f"✅ Fetched {len(scraped_data['categories'])} categories from ARCA")
        print(f"   Version: {new_version.name} (valid from {new_version.valid_from})")
        return True

    except Exception as e:
        print(f"⚠️  Failed to fetch ARCA categories: {e}")
        print("   You can manually fetch them from the Categories page")
        db.rollback()
        return False
