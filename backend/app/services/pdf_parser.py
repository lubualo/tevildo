"""
PDF parsing service for invoice data extraction.

Uses pdfplumber for text extraction and regex patterns for field extraction.
This is a "best effort" parser - it won't be perfect, but helps reduce manual entry.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from decimal import Decimal

import pdfplumber


class InvoiceParser:
    """
    Extracts invoice data from PDF files.

    Designed for Argentine AFIP invoices (Types A, B, C, E).
    """

    def __init__(self, pdf_path: Path):
        """
        Initialize parser with PDF file path.

        Args:
            pdf_path: Path to the PDF file to parse
        """
        self.pdf_path = pdf_path
        self.text = None
        self.confidence = {}  # Track confidence per field

    def parse(self) -> Dict[str, Any]:
        """
        Parse the PDF and extract invoice fields.

        Returns:
            Dictionary with extracted fields and metadata
        """
        # Extract text from PDF
        with pdfplumber.open(self.pdf_path) as pdf:
            # Most invoices are single page, but handle multiple pages
            self.text = "\n".join([page.extract_text() for page in pdf.pages])

        if not self.text:
            return {
                "success": False,
                "error": "Could not extract text from PDF",
                "confidence": 0.0,
            }

        # Extract individual fields
        result = {
            "success": True,
            "invoice_type": self._extract_invoice_type(),
            "invoice_number": self._extract_invoice_number(),
            "issue_date": self._extract_issue_date(),
            "client_name": self._extract_client_name(),
            "client_tax_id": self._extract_client_tax_id(),
            "currency": self._extract_currency(),
            "total_original": self._extract_total_original(),
            "total_ars": self._extract_total_ars(),
            "fx_rate": self._extract_fx_rate(),
            "cae": self._extract_cae(),
        }

        # Calculate overall confidence
        result["confidence"] = self._calculate_confidence()
        result["confidence_details"] = self.confidence.copy()

        return result

    def _extract_invoice_type(self) -> Optional[str]:
        """Extract invoice type (A, B, C, E, M)."""
        # Look for type marker at start of document
        # Type C: "C\nFACTURA"
        # Type E: "E\nEXPORT INVOICE"

        patterns = [
            r'ORIGINAL\s+([ABCEM])\s+(?:FACTURA|EXPORT)',  # Type at start
            r'COD\.\s+(011|019)',  # Code mapping: 011=C, 019=E
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text)
            if match:
                invoice_type = match.group(1)

                # Map codes to types for invoices
                code_map = {
                    "011": "C",
                    "019": "E",
                }
                # Note: Other codes exist (001=A, 006=B, etc.) but not in our samples

                if invoice_type in code_map:
                    invoice_type = code_map[invoice_type]

                self.confidence["invoice_type"] = 0.95
                return invoice_type

        self.confidence["invoice_type"] = 0.0
        return None

    def _extract_invoice_number(self) -> Optional[str]:
        """Extract invoice number."""
        # Type C: "Punto de Venta: 00002 Comp. Nro: 00000252"
        # Type E: "Invoice No.: 00001-00000077"

        patterns = [
            r'Invoice No\.\:\s*(\d+-\d+)',  # Type E format
            r'Punto de Venta:\s*(\d+)\s+Comp\.\s*Nro:\s*(\d+)',  # Type C format
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text)
            if match:
                if len(match.groups()) == 2:
                    # Type C: punto de venta + number → combine with dash
                    invoice_number = f"{match.group(1)}-{match.group(2)}"
                else:
                    # Type E: already has dash
                    invoice_number = match.group(1)

                self.confidence["invoice_number"] = 0.9
                return invoice_number

        self.confidence["invoice_number"] = 0.0
        return None
    
    def _extract_issue_date(self) -> Optional[str]:
        """Extract issue date and convert to ISO format (YYYY-MM-DD)."""
        # Look for: "Fecha de Emisión: 01/10/2025" or "Invoice Date: 01/10/2025"

        patterns = [
            r'Fecha de Emisión:\s*(\d{2})/(\d{2})/(\d{4})',
            r'Invoice Date:\s*(\d{2})/(\d{2})/(\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text)
            if match:
                day, month, year = match.groups()

                # Validate date
                try:
                    date_obj = datetime(int(year), int(month), int(day))
                    iso_date = date_obj.strftime("%Y-%m-%d")
                    self.confidence["issue_date"] = 0.95
                    return iso_date
                except ValueError:
                    # Invalid date
                    self.confidence["issue_date"] = 0.3
                    return None

        self.confidence["issue_date"] = 0.0
        return None

    def _extract_client_name(self) -> Optional[str]:
        """Extract client name."""
        # Type E: "Customer: Dexteel LLC"
        # Type C: Often "Consumidor Final" (skip this)

        patterns = [
            r'Customer:\s*(.+?)(?:\s+Address:|$)',  # Type E
            r'Apellido y Nombre / Razón Social:\s*(.+?)(?:\n|$)',  # Type C
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text, re.MULTILINE)
            if match:
                client_name = match.group(1).strip()

                # Skip if it's "Consumidor Final", empty, or form labels
                skip_patterns = [
                    "consumidor final",
                    "-",
                    "",
                    "condición frente al iva",
                    "condicion frente al iva",
                ]

                if client_name and client_name.lower() not in skip_patterns:
                    # Also check if it starts with common form labels
                    if not client_name.lower().startswith("condición"):
                        self.confidence["client_name"] = 0.8
                        return client_name

        self.confidence["client_name"] = 0.0
        return None

    def _extract_client_tax_id(self) -> Optional[str]:
        """Extract client CUIT."""
        # Look for CUIT near "Doc." or customer info
        # Note: Multiple CUITs in document (issuer vs client)

        # This is tricky - need to distinguish issuer CUIT from client CUIT
        # For now, skip this (too error-prone)
        self.confidence["client_tax_id"] = 0.0
        return None

    def _extract_currency(self) -> Optional[str]:
        """Extract currency code."""
        # Type E: "Currency: USD - Dólar Estadounidense"
        # Type C: Implicit ARS (peso sign)

        # Look for explicit currency
        match = re.search(r'Currency:\s*([A-Z]{3})', self.text)
        if match:
            self.confidence["currency"] = 0.95
            return match.group(1)

        # Check for peso sign or ARS keywords
        if '$' in self.text and 'USD' not in self.text:
            self.confidence["currency"] = 0.7
            return "ARS"

        self.confidence["currency"] = 0.0
        return None

    def _extract_total_original(self) -> Optional[float]:
        """Extract total in original currency (for USD/EUR invoices)."""
        currency = self._extract_currency()

        if currency == "USD":
            # Look for "Total Amount:USD 1000.00"
            match = re.search(r'Total Amount:\s*USD\s*([\d,\.]+)', self.text)
            if match:
                amount_str = match.group(1).replace(',', '')
                self.confidence["total_original"] = 0.9
                return float(amount_str)

        self.confidence["total_original"] = 0.0
        return None

    def _extract_total_ars(self) -> Optional[float]:
        """Extract total in ARS."""
        # Look for "Importe Total: $ 400000,00"
        # Argentine format: thousands with ".", decimals with ","

        patterns = [
            r'Importe Total:\s*\$\s*([\d\.]+),(\d{2})',  # Argentine format
            r'Total:\s*\$\s*([\d\.]+),(\d{2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text)
            if match:
                # Parse Argentine number format
                integer_part = match.group(1).replace('.', '')  # Remove thousand separators
                decimal_part = match.group(2)
                amount_str = f"{integer_part}.{decimal_part}"

                self.confidence["total_ars"] = 0.9
                return float(amount_str)

        self.confidence["total_ars"] = 0.0
        return None

    def _extract_fx_rate(self) -> Optional[float]:
        """Extract exchange rate (for Type E invoices)."""
        # Look for "Exchange Rate: 1380.000000"

        match = re.search(r'Exchange Rate:\s*([\d\.]+)', self.text)
        if match:
            self.confidence["fx_rate"] = 0.95
            return float(match.group(1))

        self.confidence["fx_rate"] = 0.0
        return None

    def _extract_cae(self) -> Optional[str]:
        """Extract CAE (Código de Autorización Electrónico)."""
        # Look for "CAE N°: 75409108025985"

        match = re.search(r'CAE N°:\s*(\d+)', self.text)
        if match:
            self.confidence["cae"] = 0.95
            return match.group(1)

        self.confidence["cae"] = 0.0
        return None

    def _calculate_confidence(self) -> float:
        """Calculate overall confidence score (0.0 to 1.0)."""
        if not self.confidence:
            return 0.0

        # Average of all field confidences
        total = sum(self.confidence.values())
        count = len(self.confidence)

        return round(total / count, 2) if count > 0 else 0.0
