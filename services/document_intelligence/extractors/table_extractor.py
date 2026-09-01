import re
from typing import List, Optional
from packages.shared.utils.helpers import generate_uuid
from services.document_intelligence.models import TableData


class TableExtractor:
    """Extracts tabular data from raw page text and OCR bounding box alignments."""

    def extract_tables_from_text(self, text: str, page_number: int = 1) -> List[TableData]:
        """Parse structured tabular content (Markdown tables, pipe-delimited grids, colon tables)."""
        tables: List[TableData] = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        current_table_lines: List[str] = []
        in_table = False

        for line in lines:
            # Check for pipe-delimited table line (e.g. | Col1 | Col2 |)
            if line.startswith("|") and line.endswith("|") and line.count("|") >= 3:
                # Exclude divider lines like |---|---|
                if re.match(r"^\|(\s*[-:]+\s*\|)+$", line):
                    continue
                current_table_lines.append(line)
                in_table = True
            elif in_table:
                # End of current table
                if len(current_table_lines) >= 2:
                    table = self._build_table_from_pipes(current_table_lines, page_number)
                    if table:
                        tables.append(table)
                current_table_lines = []
                in_table = False

        # Process any remaining table at end of page
        if len(current_table_lines) >= 2:
            table = self._build_table_from_pipes(current_table_lines, page_number)
            if table:
                tables.append(table)

        return tables

    def _build_table_from_pipes(self, table_lines: List[str], page_number: int) -> Optional[TableData]:
        parsed_rows: List[List[str]] = []
        for line in table_lines:
            cells = [c.strip() for c in line.strip("|").split("|")]
            parsed_rows.append(cells)

        if not parsed_rows:
            return None

        headers = parsed_rows[0]
        data_rows = parsed_rows[1:] if len(parsed_rows) > 1 else []

        return TableData(
            table_id=generate_uuid("TBL"),
            page_number=page_number,
            headers=headers,
            rows=data_rows,
            caption=f"Extracted Table (Page {page_number})",
        )
