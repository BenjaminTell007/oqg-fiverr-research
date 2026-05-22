#!/usr/bin/env python3
"""Convert docs/writers_brief.md to a styled PDF using reportlab."""

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

MD_PATH = Path("docs/writers_brief.md")
OUT_PATH = Path("docs/writers_brief.pdf")

BASE = getSampleStyleSheet()

STYLES = {
    "h1": ParagraphStyle("h1", fontSize=18, leading=22, spaceBefore=0, spaceAfter=8,
                         fontName="Helvetica-Bold", textColor=colors.HexColor("#111111")),
    "h2": ParagraphStyle("h2", fontSize=13, leading=17, spaceBefore=16, spaceAfter=4,
                         fontName="Helvetica-Bold", textColor=colors.HexColor("#222222"),
                         borderPadding=(0, 0, 2, 0)),
    "h3": ParagraphStyle("h3", fontSize=11, leading=14, spaceBefore=10, spaceAfter=2,
                         fontName="Helvetica-Bold", textColor=colors.HexColor("#333333")),
    "h4": ParagraphStyle("h4", fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=2,
                         fontName="Helvetica-BoldOblique"),
    "body": ParagraphStyle("body", fontSize=10, leading=14.5, spaceBefore=4, spaceAfter=4,
                           fontName="Helvetica", alignment=TA_LEFT),
    "li": ParagraphStyle("li", fontSize=10, leading=14, spaceBefore=1, spaceAfter=1,
                         fontName="Helvetica", leftIndent=16, bulletIndent=6),
    "meta": ParagraphStyle("meta", fontSize=9, leading=13, spaceBefore=0, spaceAfter=6,
                           fontName="Helvetica-Oblique", textColor=colors.HexColor("#555555")),
}


def inline(text: str) -> str:
    """Convert markdown inline markup to ReportLab XML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font name="Courier" size="8">\1</font>', text)
    text = text.replace("←", "&larr;")
    return text


def parse_md(md: str):
    """Parse markdown into a list of ReportLab flowables."""
    flowables = []
    lines = md.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Heading
        h_match = re.match(r"^(#{1,4})\s+(.*)", line)
        if h_match:
            level = len(h_match.group(1))
            text = inline(h_match.group(2))
            key = f"h{level}" if level <= 4 else "h4"
            flowables.append(Paragraph(text, STYLES[key]))
            i += 1
            continue

        # HR
        if re.match(r"^---+$", line):
            flowables.append(Spacer(1, 4))
            flowables.append(HRFlowable(width="100%", thickness=0.5,
                                        color=colors.HexColor("#cccccc")))
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # Table — collect all rows
        if line.startswith("|"):
            rows = []
            is_header_done = False
            header_row = None
            while i < len(lines) and lines[i].rstrip().startswith("|"):
                row_line = lines[i].rstrip()
                cells = [c.strip() for c in row_line.strip("|").split("|")]
                if all(re.match(r"^[-:]+$", c) for c in cells if c):
                    is_header_done = True
                    i += 1
                    continue
                parsed_cells = [Paragraph(inline(c), STYLES["body"]) for c in cells]
                if not is_header_done:
                    header_row = parsed_cells
                else:
                    rows.append(parsed_cells)
                i += 1

            if header_row:
                all_rows = [header_row] + rows
            else:
                all_rows = rows

            if not all_rows:
                continue

            col_count = len(all_rows[0])
            avail_width = 6.5 * inch
            col_width = avail_width / col_count

            tbl = Table(all_rows, colWidths=[col_width] * col_count,
                        repeatRows=1 if header_row else 0)
            style = [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f9f9f9")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbbbbb")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
            tbl.setStyle(TableStyle(style))
            flowables.append(Spacer(1, 4))
            flowables.append(tbl)
            flowables.append(Spacer(1, 4))
            continue

        # List item
        li_match = re.match(r"^[-*]\s+(.*)", line)
        if li_match:
            text = inline(li_match.group(1))
            flowables.append(Paragraph(f"• {text}", STYLES["li"]))
            i += 1
            continue

        # Blank line
        if line.strip() == "":
            i += 1
            continue

        # Normal paragraph — accumulate until blank or special line
        para_lines = [inline(line.strip())]
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            if (nxt.strip() == "" or nxt.startswith("#") or nxt.startswith("|")
                    or re.match(r"^[-*]\s+", nxt) or re.match(r"^---+$", nxt)):
                break
            para_lines.append(inline(nxt.strip()))
            i += 1

        text = " ".join(para_lines)
        if text.strip():
            flowables.append(Paragraph(text, STYLES["body"]))

    return flowables


def main():
    md_text = MD_PATH.read_text(encoding="utf-8")
    flowables = parse_md(md_text)

    doc = SimpleDocTemplate(
        str(OUT_PATH),
        pagesize=LETTER,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
        title="Writer's Brief — Fiverr AI Pricing Study",
        author="OQG x AISA Spring 2026",
    )
    doc.build(flowables)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
