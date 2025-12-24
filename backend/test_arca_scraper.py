"""
Test script for ARCA scraper.

Run with: docker compose exec backend python test_arca_scraper.py
"""
from app.services.arca_scraper import ARCAScraper


def main():
    print("🌐 Testing ARCA scraper...\n")

    scraper = ARCAScraper()

    try:
        result = scraper.scrape()

        print("✅ Successfully scraped ARCA data!\n")

        # Print version info
        print("📋 Version Info:")
        print(f"   Valid from: {result['version_info']['valid_from']}")
        print(f"   Notes: {result['version_info']['notes']}\n")

        # Print categories
        print(f"📊 Categories found: {len(result['categories'])}\n")
        print("="*80)

        for cat in result['categories']:
            print(f"\n🔹 Category {cat['category_letter']}:")
            print(f"   Annual Income Limit (services): ${cat['annual_income_limit_services']:,.2f}")
            print(f"   Annual Income Limit (goods):    ${cat['annual_income_limit_goods']:,.2f}")
            print(f"   Surface limit:                   {cat['surface_limit_m2']} m²")
            print(f"   Electricity limit:               {cat['electricity_limit_kwh']} kWh")
            print(f"   Annual rent limit:               ${cat['annual_rent_limit_ars']:,.2f}")
            print(f"   Integrated Tax (services):       ${cat['integrated_tax_services']:,.2f}")
            print(f"   Integrated Tax (goods):          ${cat['integrated_tax_goods']:,.2f}")
            print(f"   Pension (services):              ${cat['pension_contribution_services']:,.2f}")
            print(f"   Pension (goods):                 ${cat['pension_contribution_goods']:,.2f}")
            print(f"   Social Security (services):      ${cat['social_security_services']:,.2f}")
            print(f"   Social Security (goods):         ${cat['social_security_goods']:,.2f}")
            print(f"   📌 TOTAL Monthly (services):     ${cat['total_monthly_services']:,.2f}")
            print(f"   📌 TOTAL Monthly (goods):        ${cat['total_monthly_goods']:,.2f}")
            print("-"*80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()