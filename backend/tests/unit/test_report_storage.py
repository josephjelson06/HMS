from pathlib import Path

from app.core.storage import ReportStorage


def _sample_columns() -> list[dict[str, str]]:
    return [
        {"key": "invoice_number", "label": "Invoice"},
        {"key": "amount_cents", "label": "Amount (cents)"},
    ]


def _sample_rows() -> list[dict[str, object]]:
    return [
        {"invoice_number": "INV-1001", "amount_cents": 2000},
        {"invoice_number": "INV-1002", "amount_cents": 3500},
    ]


def test_save_csv(tmp_path: Path) -> None:
    storage = ReportStorage(str(tmp_path))
    file_path, file_name = storage.save_export(
        report_code="invoice_aging",
        export_format="csv",
        columns=_sample_columns(),
        rows=_sample_rows(),
        title="Invoice Aging",
    )

    assert file_name.endswith(".csv")
    path = Path(file_path)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Invoice" in text
    assert "INV-1001" in text


def test_save_excel(tmp_path: Path) -> None:
    storage = ReportStorage(str(tmp_path))
    file_path, file_name = storage.save_export(
        report_code="billing_snapshot",
        export_format="excel",
        columns=_sample_columns(),
        rows=_sample_rows(),
        title="Billing Snapshot",
    )

    assert file_name.endswith(".xlsx")
    path = Path(file_path)
    assert path.exists()
    # XLSX is a zip archive.
    assert path.stat().st_size > 1000


def test_save_pdf(tmp_path: Path) -> None:
    storage = ReportStorage(str(tmp_path))
    file_path, file_name = storage.save_export(
        report_code="billing_snapshot",
        export_format="pdf",
        columns=_sample_columns(),
        rows=_sample_rows(),
        title="Billing Snapshot",
    )

    assert file_name.endswith(".pdf")
    path = Path(file_path)
    assert path.exists()
    # PDF signature.
    assert path.read_bytes().startswith(b"%PDF")
