"""
Seed Monotributo categories from ARCA website.

Run with: docker compose exec backend python seed_monotributo_from_arca.py
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.database import SessionLocal
from app.models.monotributo import MonotributoCategoryVersion, MonotributoCategoryLimit
from app.services.arca_scraper import ARCAScraper


def seed_from_arca():
    """Scrape ARCA and seed database."""
    db = SessionLocal()

    try:
        print("🌐 Scraping ARCA website...")
        scraper = ARCAScraper()
        result = scraper.scrape()

        print(f"✅ Scraped {len(result['categories'])} categories")
        print(f"   Valid from: {result['version_info']['valid_from']}")

        # Check if this version already exists
        existing = (
            db.query(MonotributoCategoryVersion)
            .filter(MonotributoCategoryVersion.valid_from == result['version_info']['valid_from'])
            .first()
        )

        if existing:
            print(f"⚠️  Version already exists: {existing.name}")
            print("   Skipping seed (use delete or update manually if needed)")
            return

        # Create version
        version_id = str(uuid.uuid4())
        version = MonotributoCategoryVersion(
            id=version_id,
            name="2025-v1",  # You can update this manually if needed
            valid_from=result['version_info']['valid_from'],
            valid_to=None,  # Current version
            notes=result['version_info']['notes'],
            created_at=datetime.now(timezone.utc)
        )
        db.add(version)

        # Create category limits
        for cat_data in result['categories']:
            limit = MonotributoCategoryLimit(
                id=str(uuid.uuid4()),
                version_id=version_id,
                category_letter=cat_data['category_letter'],
                annual_income_limit_services=cat_data['annual_income_limit_services'],
                annual_income_limit_goods=cat_data['annual_income_limit_goods'],
                surface_limit_m2=cat_data['surface_limit_m2'],
                electricity_limit_kwh=cat_data['electricity_limit_kwh'],
                annual_rent_limit_ars=cat_data['annual_rent_limit_ars'],
                integrated_tax_services=cat_data['integrated_tax_services'],
                integrated_tax_goods=cat_data['integrated_tax_goods'],
                pension_contribution_services=cat_data['pension_contribution_services'],
                pension_contribution_goods=cat_data['pension_contribution_goods'],
                social_security_services=cat_data['social_security_services'],
                social_security_goods=cat_data['social_security_goods'],
                total_monthly_services=cat_data['total_monthly_services'],
                total_monthly_goods=cat_data['total_monthly_goods'],
                created_at=datetime.now(timezone.utc)
            )
            db.add(limit)

        db.commit()
        print(f"✅ Successfully seeded version: {version_id}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding Monotributo data from ARCA...")
    seed_from_arca()
    print("✨ Done!")