"""
Quick test script for the PDF parser.

Run this with:
    docker compose exec backend python test_parser.py
"""
from pathlib import Path
from app.services.pdf_parser import InvoiceParser
import json

def test_invoice(pdf_path: Path):
    """Test parser on a single invoice."""
    print(f"\n{'='*80}")
    print(f"Testing: {pdf_path.name}")
    print('='*80)

    parser = InvoiceParser(pdf_path)
    result = parser.parse()

    # Pretty print results
    print(f"\nOverall Confidence: {result['confidence']:.2f}")
    print(f"Success: {result['success']}")

    print("\n--- Extracted Fields ---")
    for field, value in result.items():
        if field not in ['success', 'confidence', 'confidence_details']:
            conf = result['confidence_details'].get(field, 0.0)
            print(f"  {field:20s}: {value} (confidence: {conf:.2f})")

    print("\n--- Full Result (JSON) ---")
    print(json.dumps(result, indent=2, default=str))

    return result

def main():
    """Test parser on sample invoices."""
    sample_dir = Path("/app/data/sample")

    # Test Type C invoice
    print("\n" + "🇦🇷 " * 40)
    print("TESTING TYPE C INVOICE (Consumer)")
    test_invoice(sample_dir / "20368713059_011_00002_00000252.pdf")

    # Test Type E invoice
    print("\n" + "🇺🇸 " * 40)
    print("TESTING TYPE E INVOICE (Export)")
    test_invoice(sample_dir / "20368713059_019_00001_00000077.pdf")

    print("\n" + "✅ " * 40)
    print("Testing complete!")

if __name__ == "__main__":
    main()
    