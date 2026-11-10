"""
PDF export for SmartWrite AI — turns the final edited text back into a
clean, downloadable PDF. Pure-Python (fpdf2), no system dependencies.
"""

from __future__ import annotations

from datetime import datetime

from fpdf import FPDF

_MARGIN = 18


class _StyledPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(20, 20, 20)
        self.cell(0, 10, self.title_text, align="L")
        self.set_draw_color(57, 255, 20)
        self.set_line_width(0.6)
        self.line(_MARGIN, 20, self.w - _MARGIN, 20)
        self.ln(14)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"SmartWrite AI  |  Page {self.page_no()}", align="C")


def export_to_pdf(text: str, title: str = "SmartWrite AI — Export") -> bytes:
    pdf = _StyledPDF(format="A4")
    pdf.title_text = title
    pdf.set_margins(_MARGIN, _MARGIN, _MARGIN)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(30, 30, 30)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Exported {datetime.now().strftime('%d %b %Y, %H:%M')}")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(30, 30, 30)
    for paragraph in text.split("\n\n"):
        pdf.multi_cell(0, 7, paragraph.strip())
        pdf.ln(4)

    return bytes(pdf.output())
