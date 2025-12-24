"""
ARCA category scraper service.
"""
import re
from decimal import Decimal
from typing import Dict, List, Optional, Any

import requests
from bs4 import BeautifulSoup

class ARCAScraper:
    ARCA_URL = "https://www.afip.gob.ar/monotributo/categorias.asp"

    def __init__(self):
        self.html_content = None
        self.soup = None

    def scrape(self) -> Dict[str, Any]:
        """
        Fetch and parse all ARCA data in one call.

        Returns:
            dict: {
                'version_info': {...},
                'categories': [...]
            }
        """
        self.fetch()

        return {
            'version_info': self.parse_version_info(),
            'categories': self.parse_categories()
        }

    def fetch(self) -> str:
        """
        Fetch HTML content from ARCA website.

        Returns:
            str: Raw HTML content

        Raises:
            requests.RequestException: If request fails
        """
        response = requests.get(self.ARCA_URL, timeout=10)
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes

        self.html_content = response.content
        self.soup = BeautifulSoup(self.html_content, 'html.parser')

        return self.html_content

    def parse_version_info(self) -> Dict[str, str]:
        """
        Extract version metadata from page.

        Looks for "Vigente desde DD/MM/YYYY" text.

        Returns:
            dict: {
                'valid_from': 'YYYY-MM-DD',
                'notes': 'Vigente desde DD/MM/YYYY - ARCA'
            }
        """
        if not self.soup:
            raise ValueError("Must call fetch() first")

        page_text = self.soup.get_text()

        # Look for "Vigente desde DD/MM/YYYY"
        date_match = re.search(r'Vigente desde (\d{1,2})/(\d{1,2})/(\d{4})', page_text)

        if date_match:
            day, month, year = date_match.groups()
            valid_from = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            notes = f"Vigente desde {day}/{month}/{year} - ARCA"
        else:
            # Fallback: use current date if we can't find it
            from datetime import date
            today = date.today()
            valid_from = today.isoformat()
            notes = f"ARCA category limits - fetched {today.isoformat()}"

        return {
            'valid_from': valid_from,
            'notes': notes
        }
    
    @staticmethod
    def _parse_ars_amount(text: str) -> Decimal:
        """
        Parse Argentine number format to Decimal.

        Examples:
            "$ 8.992.597,87" -> Decimal("8992597.87")
            "1.024.737,89" -> Decimal("1024737.89")
        """
        # Remove currency symbols, whitespace, and non-breaking spaces
        cleaned = text.replace('$', '').replace(' ', '').replace('\xa0', '').strip()

        # Handle empty or invalid input
        if not cleaned or cleaned == '-':
            return Decimal('0')

        # Replace Argentine format: . for thousands, , for decimals
        cleaned = cleaned.replace('.', '')  # Remove thousand separators
        cleaned = cleaned.replace(',', '.')  # Replace decimal separator with dot

        return Decimal(cleaned)

    @staticmethod
    def _parse_surface(text: str) -> Optional[int]:
        """
        Parse surface limit text.

        Examples:
            "Hasta 30 m²" -> 30
            "Hasta 200 m²" -> 200
        """
        match = re.search(r'(\d+)\s*m', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _parse_electricity(text: str) -> Optional[int]:
        """
        Parse electricity limit text.

        Examples:
            "Hasta 3330 Kw" -> 3330
            "Hasta 20000 Kw" -> 20000
        """
        match = re.search(r'(\d+)\s*[Kk]w', text)
        if match:
            return int(match.group(1))
        return None

    def parse_categories(self) -> List[Dict[str, Any]]:
        """
        Parse category table from ARCA page.
        """
        if not self.soup:
            raise ValueError("Must call fetch() first")

        # Find the main table
        table = self.soup.find('table')
        if not table:
            raise ValueError("Could not find category table on page")

        categories = []
        rows = table.find_all('tr')

        # Skip first 2 rows (header rows)
        for row in rows[2:]:
            cells = row.find_all('td')
            headers = row.find_all('th')

            # Skip rows that don't have enough cells
            if len(cells) < 11 or len(headers) < 1:
                continue

            try:
                # Get category letter from <th>
                category_letter = headers[0].get_text().strip()
                if category_letter not in 'ABCDEFGHIJK':
                    continue

                # Column mapping (0-indexed):
                # 0: Annual income limit
                # 1: Surface limit
                # 2: Electricity limit
                # 3: Rent limit (services)
                # 4: Max unit price for goods (we'll use as rent for goods)
                # 5: Integrated tax (services)
                # 6: Integrated tax (goods)
                # 7: Pension contribution
                # 8: Social security
                # 9: Total (services) - skip
                # 10: Total (goods) - skip

                annual_income = self._parse_ars_amount(cells[0].get_text().strip())
                surface_limit = self._parse_surface(cells[1].get_text().strip())
                electricity_limit = self._parse_electricity(cells[2].get_text().strip())
                rent_limit = self._parse_ars_amount(cells[3].get_text().strip())
                tax_services = self._parse_ars_amount(cells[5].get_text().strip())
                tax_goods = self._parse_ars_amount(cells[6].get_text().strip())
                pension = self._parse_ars_amount(cells[7].get_text().strip())
                social_security = self._parse_ars_amount(cells[8].get_text().strip())
                total_services = self._parse_ars_amount(cells[9].get_text().strip())
                total_goods = self._parse_ars_amount(cells[10].get_text().strip())

                categories.append({
                    'category_letter': category_letter,
                    'annual_income_limit_services': annual_income,
                    'annual_income_limit_goods': annual_income,
                    'surface_limit_m2': surface_limit,
                    'electricity_limit_kwh': electricity_limit,
                    'annual_rent_limit_ars': rent_limit,
                    'integrated_tax_services': tax_services,
                    'integrated_tax_goods': tax_goods,
                    'pension_contribution_services': pension,
                    'pension_contribution_goods': pension,
                    'social_security_services': social_security,
                    'social_security_goods': social_security,
                    'total_monthly_services': total_services,
                    'total_monthly_goods': total_goods,
                })

            except Exception as e:
                print(f"Warning: Could not parse category {category_letter}: {e}")
                continue

        if not categories:
            raise ValueError("No categories were successfully parsed")

        return categories