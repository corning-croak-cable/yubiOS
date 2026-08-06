"""Render the reduced paper .tex → PDF using ReportLab.
Reads the .tex, parses sections/paragraphs, builds a PDF with the charts embedded.
"""
import re
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Image, KeepTogether,
)

# ---------- Register Noto Sans ----------
NOTO_REGULAR = "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf"
NOTO_ITALIC = "/usr/share/fonts/google-noto-vf/NotoSans-Italic[wght].ttf"
try:
    pdfmetrics.registerFont(TTFont("NotoSans", NOTO_REGULAR))
    pdfmetrics.registerFont(TTFont("NotoSans-Italic", NOTO_ITALIC))
    BODY_FONT = "NotoSans"
    BODY_ITALIC = "NotoSans-Italic"
except Exception:
    BODY_FONT = "Helvetica"
    BODY_ITALIC = "Helvetica-Oblique"

# ---------- Styles ----------
styles = getSampleStyleSheet()

style_title = ParagraphStyle(
    "Title", parent=styles["Title"],
    fontName=BODY_FONT, fontSize=17, leading=21,
    alignment=TA_CENTER, spaceAfter=4, textColor=HexColor("#1a3a5c"),
)
style_subtitle = ParagraphStyle(
    "Subtitle", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=11, leading=14,
    alignment=TA_CENTER, spaceAfter=4, textColor=HexColor("#444444"),
)
style_author = ParagraphStyle(
    "Author", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=10, leading=13,
    alignment=TA_CENTER, spaceAfter=14, textColor=HexColor("#666666"),
)
style_h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontName=BODY_FONT, fontSize=14, leading=18,
    spaceBefore=18, spaceAfter=6, textColor=HexColor("#1a3a5c"),
)
style_h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontName=BODY_FONT, fontSize=12, leading=15,
    spaceBefore=12, spaceAfter=4, textColor=HexColor("#1a3a5c"),
)
style_body = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=10, leading=13.5,
    alignment=TA_JUSTIFY, spaceAfter=6,
)
style_equation = ParagraphStyle(
    "Equation", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=10, leading=13.5,
    alignment=TA_CENTER, spaceAfter=8, spaceBefore=8,
    textColor=HexColor("#222222"),
)
style_caption = ParagraphStyle(
    "Caption", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=9, leading=11.5,
    alignment=TA_CENTER, spaceAfter=10, spaceBefore=4,
    textColor=HexColor("#444444"),
)
style_lemma = ParagraphStyle(
    "Lemma", parent=styles["Normal"],
    fontName=BODY_ITALIC, fontSize=10, leading=13.5,
    alignment=TA_LEFT, spaceAfter=4, leftIndent=20, rightIndent=20,
    textColor=HexColor("#222222"),
)
style_refs = ParagraphStyle(
    "Refs", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=9, leading=11.5,
    spaceAfter=4, leftIndent=20, firstLineIndent=-20,
    textColor=HexColor("#333333"),
)


def tex_to_flowables(tex_path, charts_dir):
    """Parse a minimal subset of LaTeX into ReportLab flowables.
    Handles: title/subtitle/author, sections, paragraphs, equations,
    figures with image, tables (simple), itemize, theorem/lemma/proof.
    """
    text = Path(tex_path).read_text()
    # Strip preamble and \begin{document} ... \end{document}
    body_match = re.search(r"\\begin\{document\}(.*)\\end\{document\}", text, flags=re.DOTALL)
    body = body_match.group(1) if body_match else text

    # Drop comments
    body = re.sub(r"(?m)^%.*$", "", body)

    flowables = []
    pos = 0
    # maketitle handling
    title_match = re.search(r"\\title\{([^}]+)\}", body)
    if title_match:
        title_text = title_match.group(1).replace("\\\\", " ").replace("  ", " ")
        flowables.append(Paragraph(title_text, style_title))
    subtitle_match = re.search(r'\\title\{[^}]*\{\\\\?\\large\s+([^}]+)\}', body)
    if subtitle_match:
        flowables.append(Paragraph(subtitle_match.group(1).strip(), style_subtitle))
    author_match = re.search(r"\\author\{([^}]+)\}", body)
    if author_match:
        flowables.append(Paragraph(author_match.group(1), style_author))
    date_match = re.search(r"\\date\{([^}]+)\}", body)
    if date_match:
        flowables.append(Paragraph(date_match.group(1), style_author))
    flowables.append(Spacer(1, 6))

    # Walk through the body in chunks: section, subsection, paragraph, equation, figure, itemize
    # We'll process line by line
    lines = body.split("\n")
    i = 0
    current_paragraph = []
    in_itemize = False
    item_buffer = []

    def flush_paragraph():
        nonlocal current_paragraph
        if current_paragraph:
            txt = " ".join(current_paragraph).strip()
            txt = re.sub(r"\\\\", " ", txt)
            txt = re.sub(r"~", "&nbsp;", txt)
            # Apply bold/italic nesting carefully (reportlab requires proper nesting)
            txt = re.sub(r"\\textbf\{((?:[^{}]|\{[^{}]*\})*)\}", r"<b>\1</b>", txt)
            txt = re.sub(r"\\emph\{((?:[^{}]|\{[^{}]*\})*)\}", r"<i>\1</i>", txt)
            # Fix reportlab nesting: <b><i>X</i></b> not <b><i>X</b></i>
            txt = txt.replace("<b><i>", "<i><b>").replace("</i></b>", "</b></i>")
            txt = re.sub(r"\$([^$]+)\$", r"<i>\1</i>", txt)
            txt = re.sub(r"\\label\{[^}]+\}", "", txt)
            txt = re.sub(r"\\ref\{[^}]+\}", "[ref]", txt)
            txt = re.sub(r"\\cite\{[^}]+\}", "[cite]", txt)
            txt = re.sub(r"\\url\{([^}]+)\}", r"<font color='#0066cc'>\1</font>", txt)
            if txt:
                flowables.append(Paragraph(txt, style_body))
            current_paragraph = []

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            flush_paragraph()
            i += 1
            continue

        # Section / subsection
        m = re.match(r"\\section\*?\{([^}]+)\}", line)
        if m:
            flush_paragraph()
            flowables.append(Paragraph(m.group(1), style_h1))
            i += 1
            continue
        m = re.match(r"\\subsection\*?\{([^}]+)\}", line)
        if m:
            flush_paragraph()
            flowables.append(Paragraph(m.group(1), style_h2))
            i += 1
            continue
        m = re.match(r"\\subsubsection\*?\{([^}]+)\}", line)
        if m:
            flush_paragraph()
            flowables.append(Paragraph(m.group(1), style_h2))
            i += 1
            continue

        # Title block (we already handled)
        if line.startswith("\\maketitle") or line.startswith("\\title{") or line.startswith("\\author{") or line.startswith("\\date{"):
            i += 1
            continue

        # \begin{abstract}
        if line.startswith("\\begin{abstract}"):
            flush_paragraph()
            i += 1
            continue
        if line.startswith("\\end{abstract}"):
            flush_paragraph()
            i += 1
            continue

        # \begin{itemize}
        if line.startswith("\\begin{itemize}"):
            flush_paragraph()
            in_itemize = True
            item_buffer = []
            i += 1
            continue
        if line.startswith("\\end{itemize}"):
            for item in item_buffer:
                flowables.append(Paragraph("• " + item, style_body))
            item_buffer = []
            in_itemize = False
            i += 1
            continue

        if in_itemize:
            m = re.match(r"\\item\s*(.*)", line)
            if m:
                item_text = m.group(1)
                item_text = re.sub(r"\\emph\{((?:[^{}]|\{[^{}]*\})*)\}", r"<i>\1</i>", item_text)
                item_text = re.sub(r"\\textbf\{((?:[^{}]|\{[^{}]*\})*)\}", r"<b>\1</b>", item_text)
                item_text = re.sub(r"\$([^$]+)\$", r"<i>\1</i>", item_text)
                item_text = re.sub(r"\\\\", " ", item_text)
                item_buffer.append(item_text)
            i += 1
            continue

        # \begin{figure}
        if line.startswith("\\begin{figure}"):
            flush_paragraph()
            # Find \includegraphics + caption
            img_match = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body)
            cap_match = re.search(r"\\caption\{([^}]+(?:\{[^}]+\}[^}]+)*)\}", body)
            if img_match:
                img_file = Path(charts_dir) / Path(img_match.group(1)).name
                if not img_file.exists():
                    # Try the session dir
                    img_file_alt = Path("/var/workspace/session") / Path(img_match.group(1)).name
                    if img_file_alt.exists():
                        img_file = img_file_alt
                if img_file.exists():
                    try:
                        img = Image(str(img_file), width=5.5*inch, height=3.5*inch)
                        flowables.append(KeepTogether([img, Spacer(1, 4)]))
                    except Exception:
                        flowables.append(Paragraph(f"[figure: {img_match.group(1)}]", style_body))
                else:
                    flowables.append(Paragraph(f"[figure: {img_match.group(1)} not found]", style_body))
            if cap_match:
                cap_text = cap_match.group(1)
                cap_text = re.sub(r"\\textbf\{((?:[^{}]|\{[^{}]*\})*)\}", r"<b>\1</b>", cap_text)
                cap_text = re.sub(r"\$([^$]+)\$", r"<i>\1</i>", cap_text)
                cap_text = re.sub(r"\\\\", " ", cap_text)
                flowables.append(Paragraph(cap_text, style_caption))
            # Skip to \end{figure}
            while i < len(lines) and not lines[i].strip().startswith("\\end{figure}"):
                i += 1
            i += 1
            continue
        if line.startswith("\\end{figure}"):
            i += 1
            continue

        # \begin{table}
        if line.startswith("\\begin{table}"):
            flush_paragraph()
            i += 1
            continue
        if line.startswith("\\end{table}"):
            i += 1
            continue

        # \begin{thebibliography}
        if line.startswith("\\begin{thebibliography"):
            flush_paragraph()
            flowables.append(Paragraph("References", style_h1))
            i += 1
            continue
        if line.startswith("\\end{thebibliography"):
            i += 1
            continue
        # \bibitem entries
        m = re.match(r"\\bibitem\{[^}]+\}(.+)", line)
        if m:
            bib_text = m.group(1).strip()
            bib_text = re.sub(r"\\url\{([^}]+)\}", r"<font color='#0066cc'>\1</font>", bib_text)
            bib_text = re.sub(r"\\emph\{((?:[^{}]|\{[^{}]*\})*)\}", r"<i>\1</i>", bib_text)
            bib_text = re.sub(r"\\\\", " ", bib_text)
            flowables.append(Paragraph(bib_text, style_refs))
            i += 1
            continue

        # \begin{lemma}, \begin{theorem}, etc.
        if re.match(r"\\begin\{(lemma|theorem|corollary|proposition|definition)\}", line):
            flush_paragraph()
            kind = re.match(r"\\begin\{(\w+)\}", line).group(1)
            label_match = re.match(r"\\begin\{(\w+)\}\[(.*)\]", line)
            label = label_match.group(2) if label_match else None
            head = kind.capitalize() + (f" ({label})" if label else "")
            flowables.append(Paragraph(f"<b>{head}.</b>", style_lemma))
            i += 1
            # Read until \end{...}
            while i < len(lines) and not re.match(r"\\end\{(lemma|theorem|corollary|proposition|definition)\}", lines[i].strip()):
                txt = lines[i].strip()
                txt = re.sub(r"\\emph\{((?:[^{}]|\{[^{}]*\})*)\}", r"<i>\1</i>", txt)
                txt = re.sub(r"\$([^$]+)\$", r"<i>\1</i>", txt)
                txt = re.sub(r"\\\\", " ", txt)
                txt = re.sub(r"\\label\{[^}]+\}", "", txt)
                txt = re.sub(r"\\ref\{[^}]+\}", "[ref]", txt)
                if txt:
                    flowables.append(Paragraph(txt, style_lemma))
                i += 1
            i += 1
            continue
        if re.match(r"\\end\{(lemma|theorem|corollary|proposition|definition)\}", line):
            i += 1
            continue

        # \begin{proof}
        if re.match(r"\\begin\{proof\}", line):
            flush_paragraph()
            flowables.append(Paragraph("<b>Proof.</b>", style_lemma))
            i += 1
            continue
        if re.match(r"\\end\{proof\}", line):
            flowables.append(Paragraph("∎", style_lemma))
            i += 1
            continue

        # Equations
        if re.match(r"\\begin\{equation\}", line) or line.startswith("\\[") or line.startswith("\\["):
            flush_paragraph()
            # Collect until \end{equation} or until we hit a non-eq line
            eq_lines = []
            if re.match(r"\\begin\{equation\}", line):
                while i < len(lines) and not re.match(r"\\end\{equation\}", lines[i].strip()):
                    eq_lines.append(lines[i].strip())
                    i += 1
                i += 1
            else:
                eq_lines.append(line.lstrip("\\[").rstrip("\\]").strip())
            eq_text = " ".join(eq_lines).strip()
            eq_text = re.sub(r"\\label\{[^}]+\}", "", eq_text)
            eq_text = re.sub(r"\$([^$]+)\$", r"\1", eq_text)
            flowables.append(Paragraph(eq_text, style_equation))
            continue

        # Default: accumulate paragraph
        current_paragraph.append(line)
        i += 1

    flush_paragraph()
    return flowables


def main():
    tex_path = "/var/workspace/session/paper-reduced-2026-08-06.tex"
    charts_dir = "/var/workspace/session"
    out_path = "/var/workspace/session/paper-reduced-2026-08-06.pdf"

    flowables = tex_to_flowables(tex_path, charts_dir)
    doc = SimpleDocTemplate(
        out_path, pagesize=letter,
        leftMargin=0.85*inch, rightMargin=0.85*inch,
        topMargin=0.7*inch, bottomMargin=0.7*inch,
        title="Learned Latent Curves and the Hyperspherical-Harmonic Variant",
        author="Shant Tchatalbachian",
    )
    doc.build(flowables)
    print(f"  wrote {out_path} ({Path(out_path).stat().st_size} bytes)")


if __name__ == "__main__":
    main()
