#!/usr/bin/env python3
"""Apply deterministic memo layout to the makedoc-generated DOCX."""

from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


BODY_FONT = "Times New Roman"


def set_style_font(style, *, size: int, bold: bool | None = None) -> None:
    style.font.name = BODY_FONT
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn(f"w:{attr}"), BODY_FONT)


def set_paragraph_defaults(style, *, before: int = 0, after: int = 6, line: float = 1.08) -> None:
    fmt = style.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def add_page_field(paragraph) -> None:
    run = paragraph.add_run()
    run.font.name = BODY_FONT
    run.font.size = Pt(9)
    rpr = run._element.get_or_add_rPr()
    rfonts = OxmlElement("w:rFonts")
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn(f"w:{attr}"), BODY_FONT)
    rpr.insert(0, rfonts)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, instr, separate, text, end))


def clear_paragraph(paragraph) -> None:
    p = paragraph._element
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)


def repair(path: Path, output: Path) -> None:
    doc = Document(path)

    for section in doc.sections:
        section.orientation = WD_ORIENT.PORTRAIT
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.header_distance = Inches(0.5)
        section.footer_distance = Inches(0.5)
        section.gutter = Inches(0)

        section.footer.is_linked_to_previous = False
        footer = section.footer
        paragraph = footer.paragraphs[0]
        clear_paragraph(paragraph)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        add_page_field(paragraph)

    styles = doc.styles
    for name in ("Normal", "Body Text", "First Paragraph"):
        set_style_font(styles[name], size=11)
        set_paragraph_defaults(styles[name])

    compact = styles["Compact"]
    set_style_font(compact, size=11)
    set_paragraph_defaults(compact, after=0)

    title = styles["Title"]
    set_style_font(title, size=20, bold=True)
    set_paragraph_defaults(title, after=10, line=1.0)

    heading1 = styles["Heading 1"]
    set_style_font(heading1, size=16, bold=True)
    set_paragraph_defaults(heading1, before=14, after=6, line=1.0)

    heading2 = styles["Heading 2"]
    set_style_font(heading2, size=13, bold=True)
    set_paragraph_defaults(heading2, before=12, after=5, line=1.0)

    if doc.paragraphs:
        doc.paragraphs[0].style = title

    for paragraph in doc.paragraphs:
        if paragraph.style.name.startswith("Heading") or paragraph.style.name == "Title":
            paragraph.paragraph_format.keep_with_next = True

    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repair(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
