"""Render the reduced paper .tex → PDF using ReportLab, with proper math/nesting handling.

Reads the .tex source, parses it as a stream of environments, and emits ReportLab
flowables. This handles:
- Math mode ($...$) with brace-balanced content (math is rendered as <i>)
- Bold/italic with proper nesting (\\textbf, \\emph)
- Equations (\\begin{equation} and \\[ \\])
- Itemize lists (\\begin{itemize})
- Theorem/proof/lemma environments
- Figures with \\includegraphics + \\caption
- Bibliography (\\bibitem)
- References (\\ref, \\cite, \\url, \\label) - replaced with sensible defaults
- Section/subsection headings
- \\section*{...}, \\subsection*{...}

The parser uses proper brace-balancing for nested commands like \\textbf{$X$},
\\mathrm{...}, \\mathrm{PSL}(2,\\mathbb{C}).
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
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, KeepTogether,
)

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
style_abstract = ParagraphStyle(
    "Abstract", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=10, leading=13.5,
    alignment=TA_JUSTIFY, leftIndent=14, rightIndent=14,
    spaceBefore=4, spaceAfter=10, borderColor=HexColor("#cccccc"),
    borderWidth=0.5, borderPadding=7, backColor=HexColor("#f8f8f8"),
)
style_equation = ParagraphStyle(
    "Equation", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=10.5, leading=14,
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
style_bullet = ParagraphStyle(
    "Bullet", parent=style_body,
    leftIndent=20, bulletIndent=8, firstLineIndent=0, spaceAfter=3,
)
style_refs = ParagraphStyle(
    "Refs", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=9, leading=11.5,
    spaceAfter=4, leftIndent=20, firstLineIndent=-20,
    textColor=HexColor("#333333"),
)


def find_balanced(text, start, open_ch, close_ch):
    """Find position of matching close_ch starting at start (which is AT open_ch).
    Handles nested braces. Returns position of the matching close_ch,
    or -1 if not found.
    """
    depth = 1
    i = start + 1
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            # Skip escaped character (e.g., \{, \}, \mathrm{...})
            i += 2
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def find_matching_env(text, start, env_name):
    """Find \\end{env_name} matching \\begin{env_name} at position start.
    Returns (content_start, content_end) of the body, or None.
    """
    # start points to the \ of \begin{env_name}
    # find end of \begin{env_name}
    open_pat = "\\begin{" + env_name + "}"
    close_pat = "\\end{" + env_name + "}"
    open_start = text.find(open_pat, start)
    if open_start == -1:
        return None
    body_start = open_start + len(open_pat)
    # Find matching \end{env_name} accounting for nesting
    pos = body_start
    depth = 1
    while pos < len(text):
        next_open = text.find("\\begin{" + env_name + "}", pos)
        next_close = text.find(close_pat, pos)
        if next_close == -1:
            return None
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + len(open_pat)
        else:
            depth -= 1
            if depth == 0:
                return (body_start, next_close)
            pos = next_close + len(close_pat)
    return None


def tex_to_html(s):
    """Convert LaTeX fragment to ReportLab HTML.

    Handles:
    - $...$ math mode (italic, with brace balancing)
    - \\textbf{X}, \\emph{X} (bold/italic, with brace balancing)
    - \\ref{...}, \\cite{...}, \\label{...} (placeholder text)
    - \\url{X} (link)
    - Special chars: \\$, \\&, \\%, \\#, \\_, \\~, \\"
    - \\texttt{X} (monospace-ish: use bold for now)
    - ~ (non-breaking space)
    """
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "\\":
            # LaTeX command
            m = re.match(r"\\([a-zA-Z@]+)", s[i:])
            if m:
                cmd = m.group(1)
                j = i + len(m.group(0))
                if cmd in ("textbf", "textbf*"):
                    end = find_balanced(s, j - 1, "{", "}")
                    if end == -1:
                        i = j
                        continue
                    inner = tex_to_html(s[j:end])
                    out.append(f"<b>{inner}</b>")
                    i = end + 1
                    continue
                elif cmd in ("emph", "textit", "textit*"):
                    end = find_balanced(s, j - 1, "{", "}")
                    if end == -1:
                        i = j
                        continue
                    inner = tex_to_html(s[j:end])
                    out.append(f"<i>{inner}</i>")
                    i = end + 1
                    continue
                elif cmd in ("texttt",):
                    end = find_balanced(s, j - 1, "{", "}")
                    if end == -1:
                        i = j
                        continue
                    out.append(f"<b>{tex_to_html(s[j:end])}</b>")
                    i = end + 1
                    continue
                elif cmd in ("ref",):
                    # \ref{label} -> "[ref]"
                    end = find_balanced(s, j - 1, "{", "}")
                    if end == -1:
                        i = j
                        continue
                    label = s[j:end]
                    # Map common labels to sensible text
                    label_map = {
                        "sec:family": "\u00a72",
                        "sec:variant": "\u00a73",
                        "sec:atom": "\u00a74",
                        "sec:dataset": "\u00a75",
                        "eq:flat": "Eq.~1",
                        "eq:design": "Eq.~2",
                        "eq:hyperspherical": "Eq.~3",
                        "eq:stereographic": "Eq.~4",
                        "eq:composition": "Eq.~5",
                        "eq:loss": "Eq.~6",
                        "eq:smooth": "Eq.~7",
                        "eq:paramflat": "Eq.~8",
                        "eq:ridge": "Eq.~9",
                        "sec:family": "\u00a72",
                        "sec:mobius": "\u00a73.3",
                        "tab:context": "Table~1",
                        "tab:headline": "Table~2",
                        "fig:progression": "Figure~1",
                        "fig:per-cycle-delta": "Figure~2",
                        "fig:primitive-delta": "Figure~3",
                        "fig:atom-20cycle": "Figure~4",
                        "fig:rsi-79": "Figure~2",
                    }
                    out.append(label_map.get(label, f"[ref:{label}]"))
                    i = end + 1
                    continue
                elif cmd in ("cite",):
                    end = find_balanced(s, j - 1, "{", "}")
                    if end == -1:
                        i = j
                        continue
                    out.append(f"({s[j:end]})")
                    i = end + 1
                    continue
                elif cmd in ("label",):
                    end = find_balanced(s, j - 1, "{", "}")
                    if end == -1:
                        i = j
                        continue
                    i = end + 1  # Discard
                    continue
                elif cmd in ("url",):
                    end = find_balanced(s, j - 1, "{", "}")
                    if end == -1:
                        i = j
                        continue
                    out.append(f"<font color='#0066cc'>{s[j:end]}</font>")
                    i = end + 1
                    continue
                elif cmd in ("href",):
                    end = find_balanced(s, j - 1, "{", "}")
                    if end == -1:
                        i = j
                        continue
                    # Skip optional link text in second { }
                    next_ch = s[end + 1:end + 2] if end + 1 < n else ""
                    if next_ch == "{":
                        end2 = find_balanced(s, end + 1, "{", "}")
                        if end2 != -1:
                            out.append(f"<font color='#0066cc'>{tex_to_html(s[end + 2:end2])}</font>")
                            i = end2 + 1
                            continue
                    out.append(f"<font color='#0066cc'>{s[j:end]}</font>")
                    i = end + 1
                    continue
                elif cmd in ("S",):
                    # \S -> \u00a7 (section sign)
                    out.append("\u00a7")
                    i = j
                    continue
                elif cmd in ("%", "&", "#", "$", "_", "~", "{", "}", "\\"):
                    out.append({"%": "%", "&": "&", "#": "#", "$": "$",
                                "_": "_", "~": "\u00a0", "{": "{", "}": "}",
                                "\\": "\\"}[cmd])
                    i = j
                    continue
                elif cmd in ("mathrm", "mathbf", "mathit", "mathbb"):
                    # Treat math commands as text within italic
                    end = find_balanced(s, j - 1, "{", "}")
                    if end == -1:
                        i = j
                        continue
                    out.append(f"<i>{s[j:end]}</i>")
                    i = end + 1
                    continue
                else:
                    # Unknown command - skip it
                    i = j
                    continue
            else:
                # Single char escape
                if i + 1 < n:
                    esc = s[i + 1]
                    out.append({"%": "%", "&": "&", "#": "#", "$": "$",
                                "_": "_", "~": "\u00a0", "{": "{", "}": "}",
                                "\\": "\\"}.get(esc, s[i:i + 2]))
                    i += 2
                    continue
        elif ch == "$":
            # Math mode: $...$
            # Find matching $
            end = s.find("$", i + 1)
            if end == -1:
                out.append(ch)
                i += 1
                continue
            math_content = s[i + 1:end]
            # Convert math content: \command{X} -> italic X; just text -> italic text
            inner = tex_to_html(math_content)
            # Wrap in <i> unless already wrapped
            if inner.startswith("<i>") and inner.endswith("</i>"):
                out.append(inner)
            else:
                out.append(f"<i>{inner}</i>")
            i = end + 1
            continue
        elif ch == "~":
            out.append("\u00a0")
            i += 1
        elif ch == "<":
            out.append("&lt;")
            i += 1
        elif ch == ">":
            out.append("&gt;")
            i += 1
        elif ch == "&":
            out.append("&amp;")
            i += 1
        elif ch == "\n":
            out.append(" ")
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def render_paragraph(text):
    """Render a paragraph (may contain inline math, bold, italic)."""
    if not text.strip():
        return None
    html = tex_to_html(text.strip())
    # Normalize whitespace
    html = re.sub(r"\s+", " ", html).strip()
    return Paragraph(html, style_body)


def render_equation(text, label=None):
    """Render a numbered equation (without the label number; ReportLab can't do it cleanly)."""
    text = text.strip()
    html = tex_to_html(text)
    flowables = [Paragraph(html, style_equation)]
    if label:
        # Append label as right-aligned
        flowables.append(Paragraph(
            f"<font color='#888888' size='9'>({label})</font>",
            style_equation,
        ))
    return flowables


def render_itemize(items):
    """Render an itemize list as bullet paragraphs."""
    flowables = []
    for item in items:
        html = tex_to_html(item.strip())
        html = re.sub(r"\s+", " ", html).strip()
        flowables.append(Paragraph(html, style_bullet, bulletText="\u2022"))
    return flowables


def render_figure(image_path, caption, width=5.5*inch):
    """Render a figure with image + caption."""
    if Path(image_path).exists():
        return [
            Image(str(image_path), width=width, height=width * 0.55),
            Paragraph(tex_to_html(caption.strip()), style_caption),
        ]
    else:
        return [
            Paragraph(f"<i>[Figure: {image_path} not found]</i>", style_body),
            Paragraph(tex_to_html(caption.strip()), style_caption),
        ]


def render_lemma(kind, label, body_paragraphs, proof_paragraphs=None):
    """Render a lemma/theorem/corollary environment."""
    head = f"<b>{kind.capitalize()}{f' ({label})' if label else ''}.</b>"
    flowables = [Paragraph(head, style_lemma)]
    for p in body_paragraphs:
        html = tex_to_html(p.strip())
        flowables.append(Paragraph(html, style_lemma))
    if proof_paragraphs:
        flowables.append(Paragraph("<b>Proof.</b>", style_lemma))
        for p in proof_paragraphs:
            html = tex_to_html(p.strip())
            flowables.append(Paragraph(html, style_lemma))
        flowables.append(Paragraph("\u220e", style_lemma))
    return flowables


def render_bibitem(text):
    """Render a bibliography entry."""
    # Strip \bibitem{...} prefix
    text = re.sub(r"^\\bibitem\{[^}]+\}\s*", "", text).strip()
    html = tex_to_html(text)
    return Paragraph(html, style_refs)


def parse_paragraph(text):
    """Split text by blank lines into paragraphs, stripping comments."""
    # Drop LaTeX comments (% at start of line, or % not preceded by \)
    lines = []
    for line in text.split("\n"):
        # Drop comment lines
        if line.lstrip().startswith("%"):
            continue
        # Drop inline comments (rough: % not in math, not preceded by \)
        # Be conservative: don't drop inline % since \escapes work.
        lines.append(line)
    joined = "\n".join(lines)
    # Split into paragraphs by blank lines
    return [p.strip() for p in re.split(r"\n\s*\n", joined) if p.strip()]


def main():
    tex_path = "/var/workspace/session/paper-reduced-2026-08-06.tex"
    out_path = "/var/workspace/session/paper-reduced-2026-08-06.pdf"
    charts_dir = Path("/var/workspace/session")

    text = Path(tex_path).read_text()

    # Drop preamble
    body = re.split(r"\\begin\{document\}", text, maxsplit=1)[1]
    body = re.split(r"\\end\{document\}", body, maxsplit=1)[0]

    # Drop comments (% at start of line)
    body = re.sub(r"(?m)^%.*$", "", body)

    # Build flowables
    flowables = []

    # Title block
    title_match = re.search(r"\\title\{([^}]+(?:\{[^}]+\}[^}]+)*)\}", body)
    if title_match:
        title = title_match.group(1)
        # Drop the subtitle in {... \large ...}
        title = re.sub(r"\\\\?\{?\\large\s+([^}]+)\}?", "", title)
        title = title.replace("\\\\", " ").strip()
        flowables.append(Paragraph(title, style_title))
    author_match = re.search(r"\\author\{([^}]+)\}", body)
    if author_match:
        flowables.append(Paragraph(author_match.group(1), style_author))
    date_match = re.search(r"\\date\{([^}]+)\}", body)
    if date_match:
        flowables.append(Paragraph(date_match.group(1), style_author))
    flowables.append(Spacer(1, 6))

    # Walk body in env-aware manner
    # Strategy: split body into "before \begin{abstract}" + abstract + "main" + bibliography
    # For each, parse line-by-line, building up sections and environments

    pos = 0
    in_abstract = False
    in_itemize = False
    in_equation = False
    in_theorem_like = False
    in_proof = False
    in_figure = False
    in_table = False
    in_bibliography = False
    current_paragraph = []
    current_itemize_items = []
    current_equation = []
    current_equation_label = None
    current_theorem_body = []
    current_proof_body = []
    current_theorem_kind = "Lemma"
    current_theorem_label = None
    current_figure_image = None
    current_figure_caption = None
    current_fig_images = []
    in_caption = False

    def flush_paragraph():
        nonlocal current_paragraph
        if current_paragraph:
            joined = " ".join(current_paragraph)
            joined = re.sub(r"\s+", " ", joined).strip()
            if joined:
                # Don't render if it's a section/command start
                if not joined.startswith("\\"):
                    p = render_paragraph(joined)
                    if p:
                        flowables.append(p)
            current_paragraph = []

    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        # Begin environments
        if re.match(r"\\begin\{abstract\}", stripped):
            flush_paragraph()
            in_abstract = True
            i += 1
            continue
        if re.match(r"\\end\{abstract\}", stripped):
            flush_paragraph()
            in_abstract = False
            i += 1
            continue

        if re.match(r"\\begin\{itemize\}", stripped):
            flush_paragraph()
            in_itemize = True
            current_itemize_items = []
            i += 1
            continue
        if re.match(r"\\end\{itemize\}", stripped):
            flowables.extend(render_itemize(current_itemize_items))
            current_itemize_items = []
            in_itemize = False
            i += 1
            continue

        if re.match(r"\\begin\{enumerate\}", stripped):
            flush_paragraph()
            in_itemize = True
            current_itemize_items = []
            i += 1
            continue
        if re.match(r"\\end\{enumerate\}", stripped):
            # Render numbered list (1., 2., 3., ...) instead of bullets
            for idx, item in enumerate(current_itemize_items, start=1):
                html = tex_to_html(item.strip())
                html = re.sub(r"\s+", " ", html).strip()
                flowables.append(Paragraph(html, style_bullet, bulletText=f"{idx}."))
            current_itemize_items = []
            in_itemize = False
            i += 1
            continue

        if re.match(r"\\begin\{equation\}", stripped):
            flush_paragraph()
            in_equation = True
            current_equation = []
            current_equation_label = None
            i += 1
            continue
        if re.match(r"\\end\{equation\}", stripped):
            flowables.extend(render_equation(" ".join(current_equation),
                                              current_equation_label))
            current_equation = []
            current_equation_label = None
            in_equation = False
            i += 1
            continue

        if re.match(r"\\begin\{(lemma|theorem|corollary|proposition|definition)\}", stripped):
            flush_paragraph()
            in_theorem_like = True
            current_theorem_body = []
            current_proof_body = []
            current_theorem_kind = re.match(
                r"\\begin\{(\w+)\}", stripped).group(1).capitalize()
            label_match = re.match(
                r"\\begin\{\w+\}\[(.*)\]", stripped)
            current_theorem_label = label_match.group(1) if label_match else None
            i += 1
            continue
        if re.match(r"\\end\{(lemma|theorem|corollary|proposition|definition)\}", stripped):
            flowables.extend(render_lemma(
                current_theorem_kind,
                current_theorem_label,
                current_theorem_body,
                None,
            ))
            in_theorem_like = False
            current_theorem_body = []
            current_theorem_kind = "Lemma"
            current_theorem_label = None
            i += 1
            continue

        if re.match(r"\\begin\{proof\}", stripped):
            flush_paragraph()
            in_proof = True
            current_proof_body = []
            i += 1
            continue
        if re.match(r"\\end\{proof\}", stripped):
            flowables.append(Paragraph("\u220e", style_lemma))
            in_proof = False
            current_proof_body = []
            i += 1
            continue

        if re.match(r"\\begin\{figure\}", stripped):
            flush_paragraph()
            in_figure = True
            current_figure_image = None
            current_figure_caption = None
            i += 1
            continue
        if re.match(r"\\end\{figure\}", stripped):
            # Render figure
            if current_figure_image:
                flowables.extend(render_figure(
                    current_figure_image,
                    current_figure_caption or "",
                ))
            in_figure = False
            current_figure_image = None
            current_figure_caption = None
            i += 1
            continue

        if re.match(r"\\begin\{table\}", stripped):
            flush_paragraph()
            in_table = True
            i += 1
            continue
        if re.match(r"\\end\{table\}", stripped):
            in_table = False
            i += 1
            continue

        if stripped == "\\begin{thebibliography}" or stripped.startswith("\\begin{thebibliography"):
            flush_paragraph()
            flowables.append(Paragraph("References", style_h1))
            in_bibliography = True
            i += 1
            continue
        if stripped == "\\end{thebibliography}":
            in_bibliography = False
            i += 1
            continue

        # In environments, route appropriately
        if in_itemize:
            m = re.match(r"\\item\s*(.*)", stripped)
            if m:
                current_itemize_items.append(m.group(1))
            else:
                current_itemize_items.append(stripped)
            i += 1
            continue

        if in_equation:
            if stripped.startswith("\\label{"):
                m = re.match(r"\\label\{([^}]+)\}", stripped)
                if m:
                    current_equation_label = m.group(1)
            else:
                current_equation.append(stripped)
            i += 1
            continue

        if in_theorem_like:
            current_theorem_body.append(stripped)
            i += 1
            continue

        if in_proof:
            current_proof_body.append(stripped)
            i += 1
            continue

        if in_figure:
            if "\\includegraphics" in stripped:
                m = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", stripped)
                if m:
                    img_name = Path(m.group(1)).name
                    current_figure_image = charts_dir / img_name
                    if not current_figure_image.exists():
                        # Try session subdir
                        alt = charts_dir / "session-chart-A-H-1-progression.png"
                        if img_name == "chart-A-H-1-progression.png" and alt.exists():
                            current_figure_image = alt
            elif stripped.startswith("\\caption"):
                m = re.match(r"\\caption\{(.*)\}\s*$", stripped)
                if m:
                    current_figure_caption = m.group(1)
                else:
                    # Multi-line caption
                    current_figure_caption = stripped[8:].strip().rstrip("}")
            i += 1
            continue

        if in_bibliography:
            m = re.match(r"\\bibitem\{[^}]+\}(.*)", stripped)
            if m:
                flowables.append(render_bibitem(m.group(1)))
            i += 1
            continue

        # Section/subsection
        m = re.match(r"\\section\*?\{(.+)\}", stripped)
        if m:
            flush_paragraph()
            flowables.append(Paragraph(m.group(1).strip(), style_h1))
            i += 1
            continue
        m = re.match(r"\\subsection\*?\{(.+)\}", stripped)
        if m:
            flush_paragraph()
            flowables.append(Paragraph(m.group(1).strip(), style_h2))
            i += 1
            continue
        m = re.match(r"\\subsubsection\*?\{(.+)\}", stripped)
        if m:
            flush_paragraph()
            flowables.append(Paragraph(m.group(1).strip(), style_h2))
            i += 1
            continue

        # \maketitle, \title{}, \author{}, \date{} - already handled
        if stripped.startswith("\\maketitle"):
            i += 1
            continue
        if stripped.startswith("\\title{") or stripped.startswith("\\author{") or stripped.startswith("\\date{"):
            i += 1
            continue

        # Default: accumulate paragraph (in main body)
        if stripped.startswith("\\"):
            # Other commands - flush, skip
            i += 1
            continue
        current_paragraph.append(stripped)
        i += 1

    flush_paragraph()

    doc = SimpleDocTemplate(
        str(out_path), pagesize=letter,
        leftMargin=0.85*inch, rightMargin=0.85*inch,
        topMargin=0.7*inch, bottomMargin=0.7*inch,
        title="Learned Latent Curves and the Hyperspherical-Harmonic Variant (Reduced, 2026-08-06)",
        author="Shant Tchatalbachian",
    )
    doc.build(flowables)
    print(f"  wrote {out_path} ({Path(out_path).stat().st_size} bytes)")


if __name__ == "__main__":
    main()
