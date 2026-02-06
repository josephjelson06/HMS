import csv
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

import xlsxwriter
from fpdf import FPDF


class ReportStorage:
    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)

    def save_export(
        self,
        report_code: str,
        export_format: str,
        columns: Iterable[dict[str, str]],
        rows: Iterable[dict[str, object]],
        title: str | None = None,
    ) -> tuple[str, str]:
        export_format = export_format.lower()
        if export_format == "csv":
            return self.save_csv(report_code, columns, rows)
        if export_format == "excel":
            return self.save_excel(report_code, columns, rows)
        if export_format == "pdf":
            return self.save_pdf(report_code, columns, rows, title=title)
        raise ValueError("Unsupported export format")

    def save_csv(
        self,
        report_code: str,
        columns: Iterable[dict[str, str]],
        rows: Iterable[dict[str, object]],
    ) -> tuple[str, str]:
        self.base_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        file_name = f"{report_code}-{timestamp}.csv"
        file_path = self.base_path / file_name

        header, keys = self._header_and_keys(columns)

        with file_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            for row in rows:
                writer.writerow([self._format_value(row.get(key)) for key in keys])

        return str(file_path), file_name

    def save_excel(
        self,
        report_code: str,
        columns: Iterable[dict[str, str]],
        rows: Iterable[dict[str, object]],
    ) -> tuple[str, str]:
        self.base_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        file_name = f"{report_code}-{timestamp}.xlsx"
        file_path = self.base_path / file_name

        header, keys = self._header_and_keys(columns)
        workbook = xlsxwriter.Workbook(str(file_path))
        worksheet = workbook.add_worksheet("Report")

        header_format = workbook.add_format({"bold": True, "bg_color": "#EFEFEF"})
        for col_index, label in enumerate(header):
            worksheet.write(0, col_index, label, header_format)

        for row_index, row in enumerate(rows, start=1):
            for col_index, key in enumerate(keys):
                worksheet.write(row_index, col_index, self._format_value(row.get(key)))

        for col_index, label in enumerate(header):
            width = min(max(len(label) + 2, 14), 40)
            worksheet.set_column(col_index, col_index, width)

        workbook.close()
        return str(file_path), file_name

    def save_pdf(
        self,
        report_code: str,
        columns: Iterable[dict[str, str]],
        rows: Iterable[dict[str, object]],
        title: str | None = None,
    ) -> tuple[str, str]:
        self.base_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        file_name = f"{report_code}-{timestamp}.pdf"
        file_path = self.base_path / file_name

        header, keys = self._header_and_keys(columns)

        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 8, title or report_code, new_x="LMARGIN", new_y="NEXT")

        if not keys:
            pdf.set_font("Helvetica", size=10)
            pdf.cell(0, 8, "No tabular data available for this report.", new_x="LMARGIN", new_y="NEXT")
            pdf.output(str(file_path))
            return str(file_path), file_name

        usable_width = pdf.w - pdf.l_margin - pdf.r_margin
        col_width = max(22.0, usable_width / len(keys))

        pdf.set_font("Helvetica", size=9)
        for label in header:
            pdf.cell(col_width, 7, self._truncate(str(label), 28), border=1)
        pdf.ln(7)

        for row in rows:
            for key in keys:
                text = self._truncate(self._format_value(row.get(key)), 30)
                pdf.cell(col_width, 6, text, border=1)
            pdf.ln(6)

        pdf.output(str(file_path))
        return str(file_path), file_name

    @staticmethod
    def _header_and_keys(columns: Iterable[dict[str, str]]) -> tuple[list[str], list[str]]:
        column_list = list(columns)
        header = [col.get("label", col.get("key", "")) for col in column_list]
        keys = [col.get("key", "") for col in column_list]
        return header, keys

    @staticmethod
    def _truncate(value: str, max_chars: int) -> str:
        if len(value) <= max_chars:
            return value
        return value[: max_chars - 3] + "..."

    @staticmethod
    def _format_value(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)
