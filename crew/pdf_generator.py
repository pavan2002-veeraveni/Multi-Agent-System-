"""
Programmatic PDF Report Generator

Compiles a formatted A4 PDF report using ReportLab containing:
  - Professional header banner with document metadata
  - Styled sections with the writer's report copy
  - Tabular grid rendering of Pandas summary statistics
  - Automatic page numbering (Page X of Y) and footer notes
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
PRIMARY_COLOR = HexColor("#1a237e")     # Deep indigo
SECONDARY_COLOR = HexColor("#283593")   # Slightly lighter indigo
ACCENT_COLOR = HexColor("#42a5f5")      # Light blue accent
HEADER_BG = HexColor("#1a237e")
TABLE_HEADER_BG = HexColor("#1a237e")
TABLE_ALT_ROW = HexColor("#e8eaf6")
BORDER_COLOR = HexColor("#c5cae9")


# ---------------------------------------------------------------------------
# NumberedCanvas — implements "Page X of Y"
# ---------------------------------------------------------------------------

class NumberedCanvas(canvas.Canvas):
    """Custom canvas that supports 'Page X of Y' numbering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict] = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(num_pages)
            super().showPage()
        super().save()

    def _draw_page_number(self, page_count: int) -> None:
        width, height = A4
        self.setFont("Helvetica", 9)
        self.setFillColor(grey)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(width - 2 * cm, 1.5 * cm, page_text)

        # Footer note on the left
        self.drawString(
            2 * cm, 1.5 * cm,
            "Multi-Agent Market Research & Report Generator | Confidential",
        )

        # Thin separator line above footer
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(2 * cm, 2 * cm, width - 2 * cm, 2 * cm)


# ---------------------------------------------------------------------------
# MarketReportPDF
# ---------------------------------------------------------------------------

class MarketReportPDF:
    """Builds a professional A4 PDF report from Markdown content."""

    def __init__(
        self,
        filename: str = "output/market_report.pdf",
        title: str = "Market Research Report",
        author: str = "Multi-Agent Research Team",
        query: str = "",
    ):
        self.filename = filename
        self.title = title
        self.author = author
        self.query = query
        self.elements: list = []
        self.styles = getSampleStyleSheet()
        self._register_custom_styles()

    # ----- custom styles --------------------------------------------------

    def _register_custom_styles(self) -> None:
        """Add custom ParagraphStyles to the stylesheet."""
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=self.styles["Title"],
            fontSize=26,
            leading=32,
            textColor=white,
            alignment=TA_CENTER,
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            name="ReportSubtitle",
            parent=self.styles["Normal"],
            fontSize=13,
            leading=18,
            textColor=HexColor("#e8eaf6"),
            alignment=TA_CENTER,
            spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeading",
            parent=self.styles["Heading1"],
            fontSize=16,
            leading=22,
            textColor=PRIMARY_COLOR,
            spaceBefore=18,
            spaceAfter=10,
            borderWidth=0,
            borderPadding=0,
        ))
        self.styles.add(ParagraphStyle(
            name="SubHeading",
            parent=self.styles["Heading2"],
            fontSize=13,
            leading=18,
            textColor=SECONDARY_COLOR,
            spaceBefore=12,
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            name="BodyText2",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=15,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name="BulletItem",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=15,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            name="MetaInfo",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=HexColor("#b0bec5"),
            alignment=TA_CENTER,
        ))

    # ----- header banner --------------------------------------------------

    def add_header_banner(self) -> None:
        """Add a professional coloured header banner with metadata."""
        width, _ = A4
        usable = width - 4 * cm

        # Banner table (single-cell table with background colour)
        generated_date = datetime.now().strftime("%B %d, %Y at %H:%M")
        banner_data = [[
            Paragraph(f"<b>{self.title}</b>", self.styles["ReportTitle"]),
        ], [
            Paragraph(
                f"Query: {self.query}" if self.query else "Automated Market Analysis",
                self.styles["ReportSubtitle"],
            ),
        ], [
            Paragraph(
                f"Generated: {generated_date} &nbsp;|&nbsp; Author: {self.author}",
                self.styles["MetaInfo"],
            ),
        ]]

        banner = Table(banner_data, colWidths=[usable])
        banner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEADER_BG),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, 0), 30),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 25),
            ("LEFTPADDING", (0, 0), (-1, -1), 20),
            ("RIGHTPADDING", (0, 0), (-1, -1), 20),
            ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ]))

        self.elements.append(banner)
        self.elements.append(Spacer(1, 20))

    # ----- section helpers -----------------------------------------------

    def add_section(self, heading: str, body: str) -> None:
        """Add a styled heading followed by body paragraphs."""
        # Coloured underline bar under heading
        self.elements.append(Paragraph(heading, self.styles["SectionHeading"]))

        # Underline
        line_data = [["" ]]
        line_table = Table(line_data, colWidths=[A4[0] - 4 * cm])
        line_table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 1.5, ACCENT_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        self.elements.append(line_table)
        self.elements.append(Spacer(1, 6))

        # Parse body lines
        for line in body.split("\n"):
            stripped = line.strip()
            if not stripped:
                self.elements.append(Spacer(1, 6))
                continue
            if stripped.startswith(("- ", "• ", "* ")):
                bullet_text = stripped.lstrip("-•* ").strip()
                self.elements.append(
                    Paragraph(f"•  {bullet_text}", self.styles["BulletItem"])
                )
            elif stripped.startswith("## "):
                self.elements.append(
                    Paragraph(stripped.lstrip("# ").strip(), self.styles["SubHeading"])
                )
            else:
                self.elements.append(
                    Paragraph(stripped, self.styles["BodyText2"])
                )

    # ----- data table ----------------------------------------------------

    def add_data_table(self, markdown_table: str, caption: str = "Summary Statistics") -> None:
        """
        Parse a Markdown table and render it as a styled ReportLab Table.

        Args:
            markdown_table: Markdown-formatted table string.
            caption: Caption text displayed above the table.
        """
        lines = [l.strip() for l in markdown_table.strip().split("\n") if l.strip()]

        # Filter out separator lines (e.g. |---|---|)
        data_lines = [l for l in lines if not re.match(r"^\|[\s\-:]+\|$", l)]

        if not data_lines:
            self.elements.append(
                Paragraph("No tabular data available.", self.styles["BodyText2"])
            )
            return

        # Parse pipe-delimited rows
        table_data: list[list[str]] = []
        for line in data_lines:
            cells = [c.strip() for c in line.strip("|").split("|")]
            table_data.append(cells)

        if not table_data:
            return

        # Caption
        self.elements.append(Spacer(1, 10))
        self.elements.append(
            Paragraph(f"<b>{caption}</b>", self.styles["SubHeading"])
        )
        self.elements.append(Spacer(1, 6))

        # Wrap cell text in Paragraphs for word wrapping
        col_count = len(table_data[0]) if table_data else 1
        usable_width = A4[0] - 4 * cm
        col_width = usable_width / col_count

        styled_data: list[list] = []
        for row_idx, row in enumerate(table_data):
            styled_row = []
            for cell in row:
                style = self.styles["BodyText2"] if row_idx > 0 else self.styles["Normal"]
                styled_row.append(Paragraph(str(cell), style))
            styled_data.append(styled_row)

        table = Table(styled_data, colWidths=[col_width] * col_count, repeatRows=1)

        # Build style commands
        style_cmds = [
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            # Body
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]

        # Alternate row colours
        for i in range(1, len(styled_data)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW))

        table.setStyle(TableStyle(style_cmds))
        self.elements.append(table)
        self.elements.append(Spacer(1, 12))

    # ----- build PDF ------------------------------------------------------

    def build(self) -> str:
        """
        Compile all elements into the final PDF file.

        Returns:
            Absolute path to the generated PDF.
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.filename) or ".", exist_ok=True)

        width, height = A4
        frame = Frame(
            2 * cm, 2.5 * cm,
            width - 4 * cm, height - 5 * cm,
            id="main_frame",
        )

        page_template = PageTemplate(
            id="main",
            frames=[frame],
        )

        doc = BaseDocTemplate(
            self.filename,
            pagesize=A4,
            pageTemplates=[page_template],
            title=self.title,
            author=self.author,
        )

        doc.build(self.elements, canvasmaker=NumberedCanvas)

        abs_path = os.path.abspath(self.filename)
        logger.info("PDF report generated: %s", abs_path)
        return abs_path

    # ----- convenience: build from markdown text --------------------------

    @classmethod
    def from_markdown(
        cls,
        markdown_text: str,
        filename: str = "output/market_report.pdf",
        title: str = "Market Research Report",
        query: str = "",
        statistics_markdown: str | None = None,
    ) -> str:
        """
        Parse a Markdown report into sections and compile the PDF.

        Args:
            markdown_text:        The full report in Markdown.
            filename:             Output PDF path.
            title:                Document title.
            query:                Original search query.
            statistics_markdown:  Optional Pandas statistics table in Markdown.

        Returns:
            Absolute path to the generated PDF.
        """
        pdf = cls(filename=filename, title=title, query=query)
        pdf.add_header_banner()

        # Split by top-level headings (# Heading)
        sections = re.split(r"(?m)^#{1,2}\s+", markdown_text)

        # First chunk (before any heading) is treated as preamble
        heading_matches = re.findall(r"(?m)^#{1,2}\s+(.+)", markdown_text)

        for idx, section_body in enumerate(sections):
            body = section_body.strip()
            if not body:
                continue

            if idx == 0 and not heading_matches:
                # Preamble without a heading
                pdf.add_section("Overview", body)
            elif idx == 0:
                # Content before the first heading
                if body:
                    pdf.add_section("Overview", body)
            else:
                heading = heading_matches[idx - 1] if idx - 1 < len(heading_matches) else f"Section {idx}"
                # Check if this section contains a markdown table
                if "|" in body and "---" in body:
                    # Split into text and table parts
                    table_lines = []
                    text_lines = []
                    in_table = False
                    for line in body.split("\n"):
                        if "|" in line and not in_table:
                            in_table = True
                        if in_table and "|" in line:
                            table_lines.append(line)
                        elif in_table and "|" not in line:
                            in_table = False
                            text_lines.append(line)
                        else:
                            text_lines.append(line)

                    if text_lines:
                        pdf.add_section(heading, "\n".join(text_lines))
                    if table_lines:
                        pdf.add_data_table("\n".join(table_lines), caption=heading)
                else:
                    pdf.add_section(heading, body)

        # Add standalone statistics table if provided
        if statistics_markdown:
            pdf.add_data_table(statistics_markdown, caption="Financial Summary Statistics")

        return pdf.build()
