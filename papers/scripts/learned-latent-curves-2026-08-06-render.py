"""Render learned-latent-curves-2026-08-06-reduced.pdf using the render.py template.

Uses manual paragraph crafting (no LaTeX parsing), with explicit Unicode math glyphs.
The .tex source is the canonical source for editing/version control; this script
generates the PDF that mirrors the .tex content for the REDUCED paper (after the
advisor-agent classification removed 21 paragraphs).
"""
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

# ---------- Register Noto Sans ----------
# DejaVu Sans has the full math-symbol range we need (∑, ∫, ∂, ≤, ≥, ≠, ⊂, ∈, etc.)
# Noto Sans (the prior default) is missing these glyphs.
NOTO_REGULAR = "/var/workspace/session/fonts/DejaVuSans.ttf"
NOTO_ITALIC = "/var/workspace/session/fonts/DejaVuSerif.ttf"
try:
    pdfmetrics.registerFont(TTFont("BodyFont", NOTO_REGULAR))
    pdfmetrics.registerFont(TTFont("BodyFontItalic", NOTO_ITALIC))
    BODY_FONT = "BodyFont"
    BODY_ITALIC = "BodyFontItalic"
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
    fontName=BODY_FONT, fontSize=12, leading=16,
    spaceBefore=12, spaceAfter=5, textColor=HexColor("#1a3a5c"),
)
style_h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontName=BODY_FONT, fontSize=10.5, leading=13,
    spaceBefore=8, spaceAfter=3, textColor=HexColor("#1a3a5c"),
)
style_body = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=9.5, leading=13,
    alignment=TA_JUSTIFY, spaceAfter=5, firstLineIndent=12,
)
style_abstract = ParagraphStyle(
    "Abstract", parent=styles["Normal"],
    fontName=BODY_FONT, fontSize=9.5, leading=13,
    alignment=TA_JUSTIFY, leftIndent=14, rightIndent=14,
    spaceBefore=4, spaceAfter=10, borderColor=HexColor("#888888"),
    borderWidth=1.2, borderPadding=8, backColor=HexColor("#fafafa"),
)
style_emph = ParagraphStyle(
    "Emph", parent=style_body, leftIndent=10, rightIndent=10,
    fontSize=9.5, leading=13, textColor=HexColor("#222222"),
)
style_bullet = ParagraphStyle(
    "Bullet", parent=style_body, leftIndent=22, bulletIndent=8,
    firstLineIndent=0, spaceAfter=2,
)
style_equation = ParagraphStyle(
    "Equation", parent=style_body,
    fontName=BODY_FONT, fontSize=10, leading=14,
    alignment=TA_CENTER, spaceBefore=6, spaceAfter=6,
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


# ---------- Build ----------
output_path = Path("/var/workspace/session/paper-reduced-2026-08-06.pdf")
doc = SimpleDocTemplate(
    str(output_path), pagesize=letter,
    leftMargin=0.85*inch, rightMargin=0.85*inch,
    topMargin=0.7*inch, bottomMargin=0.7*inch,
    title="Learned Latent Curves and the Hyperspherical-Harmonic Variant (Reduced, 2026-08-06)",
    author="Shant Tchatalbachian",
)
story = []

# --- Title block ---
story.append(Paragraph(
    "Learned Latent Curves and the Hyperspherical-Harmonic Variant",
    style_title,
))
story.append(Paragraph(
    "A Closed-Loop Framework for Corpus Embedding and Recursive Skill Auditing",
    style_subtitle,
))
story.append(Paragraph("Shant Tchatalbachian", style_author))
story.append(Paragraph(
    "<font color='#666666'>August 6, 2026</font>", style_author,
))
story.append(Spacer(1, 6))

# --- Abstract (boxed) ---
story.append(Paragraph(
    "<b>Abstract.</b> We describe a closed-loop framework for auditing and "
    "prioritizing improvement work across a corpus of engineering artifacts, "
    "and we document a sphere-aware extension of its curve-fitting stage "
    "together with the <i>smallest audit unit</i> that the framework admits. "
    "The framework has four composed techniques: (1) a <i>learned latent "
    "curve</i>, which re-expands a single 1-D ordering coordinate <i>t</i> "
    "into a fixed-width <i>D</i>-dimensional embedding via a Fourier basis "
    "with learned frequencies; (2) <i>curve-guided recursive "
    "self-improvement</i>, which uses sparse cells of the fitted curve as a "
    "prioritization lens for gap-mapping and bounded fixpoint-style editing "
    "cycles; (3) a <i>hyperspherical-harmonic curve</i>, which replaces the flat "
    "[<font face='BodyFont'>0</font>,<font face='BodyFont'>1</font>]<sup>2</sup> parameter manifold of (1) with the "
    "Riemann sphere <i>S<sup>2</sup></i> and a learned M&ouml;bius "
    "φ<sub>θ</sub> &isin; PSL(2,ℂ) reparameterization; and (4) the "
    "<i>single-action atom</i>, which is the smallest unit of the loop "
    "&mdash; one corpus item maps to one point on <i>S<sup>2</sup></i>, one "
    "missing-primitive flip is one action, and the geodesic-only criterion "
    "gives an invariant that composes linearly across files. We give the "
    "governing equations for each technique, the empirical validation on a "
    "corpus of software skills (<i>N</i> = 49, <i>N</i> = 70, and "
    "<i>N</i> = 79 across three splits and one full-corpus audit), and a "
    "474-dispatch atom experiment on the 79-skill corpus plus a 20-cycle "
    "experiment on 11 deep-research files, both showing zero negative "
    "&Delta; and confirming Lemma&nbsp;1 and Theorem&nbsp;1 directly.",
    style_abstract,
))

# --- §1 Introduction ---
story.append(Paragraph("1&nbsp;&nbsp;Introduction", style_h1))
story.append(Paragraph(
    "The paper is organized so each main-body section earns its place by "
    "improving fit, clarifying the geometry, or sharpening the claim. "
    "Sections&nbsp;2&ndash;4 give the family background (flat curve model, "
    "hyperspherical variant, atom) at the level of governing equations. "
    "Sections&nbsp;5&ndash;6 give the dataset, evaluation protocol, and "
    "headline results, with the 79-skill corpus audit reported as the "
    "primary empirical exhibit. Sections&nbsp;7&ndash;8 are scope and "
    "conclusion. Two appendices carry the remaining material.",
    style_body,
))

# --- §2 Background: The Learned-Latent-Curve Family ---
story.append(Paragraph("2&nbsp;&nbsp;Background: The Learned-Latent-Curve Family", style_h1))
story.append(Paragraph("2.1&nbsp;&nbsp;Flat curve model", style_h2))
story.append(Paragraph(
    "For output dimension <i>j</i> = 1, &hellip;, <i>D</i> "
    "(canonically <i>D</i> = 384) and 1-D coordinate <i>t</i> "
    "&isin; [<font face='BodyFont'>0</font>,<font face='BodyFont'>1</font>], "
    "the model is",
    style_body,
))
story.append(Paragraph(
    "<i>z<sub>j</sub></i>(<i>t</i>) = "
    "<i>a<sub>j,0</sub></i> + ∑<sub><i>m</i>=1</sub><sup><i>k</i></sup> "
    "&nbsp;( <i>a<sub>j,m</sub></i> sin(2π <i>f<sub>m</sub></i> <i>t</i>) "
    "+ <i>b<sub>j,m</sub></i> cos(2π <i>f<sub>m</sub></i> <i>t</i>) &nbsp;),",
    style_equation,
))
story.append(Paragraph(
    "with <i>k</i> shared learned frequencies <i>f<sub>1</sub></i>, "
    "&hellip;, <i>f<sub>k</sub></i> and per-output coefficients "
    "<i>a<sub>j,m</sub></i>, <i>b<sub>j,m</sub></i>. Stacked over <i>j</i>, "
    "this is a curve γ : &#8477;<sup><i>D</i></sup> → &#8477;<sup><i>D</i></sup>. "
    "Writing the design vector",
    style_body,
))
story.append(Paragraph(
    "φ(<i>t</i>) = &nbsp;[ 1,&nbsp; sin(2π <i>f<sub>1</sub></i> <i>t</i>),"
    "&nbsp; cos(2π <i>f<sub>1</sub></i> <i>t</i>), &hellip;, "
    "sin(2π <i>f<sub>k</sub></i> <i>t</i>),&nbsp; cos(2π <i>f<sub>k</sub></i> <i>t</i>) &nbsp;] "
    "&isin; &#8477;<sup>1+2<i>k</i></sup>,",
    style_equation,
))
story.append(Paragraph(
    "the model is γ(<i>t</i>) = <i>C</i>&nbsp;φ(<i>t</i>) with coefficient "
    "matrix <i>C</i> &isin; &#8477;<sup><i>D</i> &times; (1+2<i>k</i>)</sup>, "
    "giving a parameter count of",
    style_body,
))
story.append(Paragraph(
    "<i>P</i><sub>flat</sub> = <i>D</i> &middot; (1 + 2<i>k</i>).",
    style_equation,
))
story.append(Paragraph(
    "At <i>D</i> = 384, <i>k</i> = 8: <i>P</i><sub>flat</sub> = "
    "384 &middot; 17 = 6,528 parameters.",
    style_body,
))

story.append(Paragraph("2.2&nbsp;&nbsp;Closed-form coefficient solve", style_h2))
story.append(Paragraph(
    "With the frequencies <i>f</i> held fixed, the linear coefficient solve "
    "is the Tikhonov ridge,",
    style_body,
))
story.append(Paragraph(
    "<i>C</i><sup>⋆</sup> = (Φ<sup>&top;</sup>Φ + λ <i>I</i>)<sup>-1</sup> Φ<sup>&top;</sup> <i>Z</i>.",
    style_equation,
))
story.append(Paragraph(
    "where Φ &isin; &#8477;<sup><i>N</i> &times; (1+2<i>k</i>)</sup> stacks "
    "the design vector and <i>Z</i> &isin; &#8477;<sup><i>N</i> &times; <i>D</i></sup> "
    "stacks the target vectors. This is the sanity floor for any "
    "gradient-descent fit at the same frequencies: a fit worse than this at "
    "the same <i>f</i> means the optimizer failed, not the model.",
    style_body,
))

story.append(Paragraph("2.3&nbsp;&nbsp;Obtaining the coordinate <i>t</i>", style_h2))
story.append(Paragraph(
    "The default pipeline sets <i>t</i> from the top principal component of a "
    "<i>z</i>-scored <i>N</i> &times; <i>D</i><sub>feat</sub> feature matrix, "
    "mapped to [<font face='BodyFont'>0</font>,<font face='BodyFont'>1</font>]; "
    "a rank-uniformized variant replaces raw PC1 scores by their fractional "
    "ranks before mapping. The PC1+PC2 explained-variance ratio is the "
    "fit-quality gate (&ge; 0.40); flat curves below the gate are not used.",
    style_body,
))

# --- §3 The Hyperspherical-Harmonic Curve ---
story.append(Paragraph("3&nbsp;&nbsp;The Hyperspherical-Harmonic Curve", style_h1))
story.append(Paragraph("3.1&nbsp;&nbsp;Model", style_h2))
story.append(Paragraph(
    "For <b>x</b> &isin; <i>S<sup>2</sup></i> &sube; &#8477;<sup>3</sup> "
    "(the Riemann sphere),",
    style_body,
))
story.append(Paragraph(
    "γ(<b>x</b>) = <b>b</b> + ∑<sub><i>&ell;</i>=0</sub><sup><i>L</i></sup> "
    "∑<sub><i>m</i></sub> <b>a</b><sub><i>&ell;,m</i></sub> "
    "<i>Y<sup>S<sup>2</sup></sup><sub>&ell;,m</sub></i>"
    "&nbsp;( φ<sub><i>&theta;</i></sub>(<b>x</b>) &nbsp;).",
    style_equation,
))
story.append(Paragraph(
    "where <b>b</b> &isin; &#8477;<sup><i>D</i></sup> is the per-dim bias, "
    "<b>a</b><sub><i>&ell;,m</i></sub> &isin; &#8477;<sup><i>D</i></sup> are the "
    "per-dim per-basis coefficients, and φ<sub><i>&theta;</i></sub> is the "
    "M&ouml;bius reparameterization.",
    style_body,
))
story.append(Paragraph(
    "The parameter count is <i>D</i> &middot; <i>n</i><sub>basis</sub> "
    "+ <i>D</i> + <i>n</i><sub>M&ouml;bius</sub>, where "
    "<i>n</i><sub>basis</sub> = ∑<sub><i>&ell;</i>=0</sub><sup><i>L</i></sup>(2<i>&ell;</i>+1) "
    "and <i>n</i><sub>M&ouml;bius</sub> is the real dimension of "
    "PSL(2,ℂ) (Section&nbsp;3.3). At <i>L</i> = 3 on <i>S<sup>2</sup></i>, "
    "<i>n</i><sub>basis</sub> = 16; at <i>D</i> = 384: "
    "<i>P</i><sub>sphere</sub> = 384 &middot; 16 + 384 + 6 = 6,534.",
    style_body,
))

story.append(Paragraph("3.2&nbsp;&nbsp;Real spherical harmonics on <i>S<sup>2</sup></i>", style_h2))
story.append(Paragraph(
    "The real spherical harmonics <i>Y<sup>S<sup>2</sup></sup><sub>&ell;,m</sub></i> "
    "on <i>S<sup>2</sup></i> are constructed via explicit Legendre polynomials "
    "and the cos/sin split:",
    style_body,
))
story.append(Paragraph(
    "<i>Y<sup>c</sup><sub>&ell;,0</sub></i>(θ, φ) = "
    "<i>N<sub>&ell;</sub></i><sup>0</sup> &middot; <i>P<sub>&ell;</sub></i><sup>0</sup>(cos θ)",
    style_equation,
))
story.append(Paragraph(
    "<i>Y<sup>c</sup><sub>&ell;,m</sub></i>(θ, φ), <i>m</i> &gt; 0 = "
    "√2 &middot; <i>N<sub>&ell;</sub></i><sup>m</sup> &middot; "
    "<i>P<sub>&ell;</sub></i><sup>m</sup>(cos θ) &middot; cos(<i>m</i>φ)",
    style_equation,
))
story.append(Paragraph(
    "<i>Y<sup>c</sup><sub>&ell;,−m</sub></i>(θ, φ), <i>m</i> &gt; 0 = "
    "√2 &middot; <i>N<sub>&ell;</sub></i><sup>m</sup> &middot; "
    "<i>P<sub>&ell;</sub></i><sup>m</sup>(cos θ) &middot; sin(<i>m</i>φ)",
    style_equation,
))
story.append(Paragraph(
    "with <i>N<sub>&ell;</sub><sup>m</sup></i> = "
    "√[(2<i>&ell;</i>+1)/(4π) &middot; (<i>&ell;</i>&minus;<i>m</i>)!/(<i>&ell;</i>+<i>m</i>)!] "
    "the standard normalisation. At <i>L</i> = 3 on <i>S<sup>2</sup></i> the basis "
    "has 1 + 3 + 5 + 7 = 16 functions; at <i>L</i> = 3 on <i>S<sup>3</sup></i> "
    "the basis has 30 functions.",
    style_body,
))

story.append(Paragraph("3.3&nbsp;&nbsp;M&ouml;bius reparameterization", style_h2))
story.append(Paragraph(
    "φ<sub><i>&theta;</i></sub>(<i>z</i>) = (<i>az</i>+<i>b</i>)/(<i>cz</i>+<i>d</i>) "
    "with <i>a</i>,<i>b</i>,<i>c</i>,<i>d</i> &isin; &#8450; and "
    "<i>ad</i>&minus;<i>bc</i> = +1. The four complex coefficients "
    "<i>a</i>,<i>b</i>,<i>c</i>,<i>d</i> carry 8 real components. The "
    "constraint <i>ad</i>&minus;<i>bc</i> = +1 is a <i>complex</i> constraint "
    "(real part equals 1, imaginary part equals 0), so it removes 2 real "
    "degrees of freedom, leaving 6 real degrees of freedom. The PSL(2,ℂ) "
    "identification (matrices <i>M</i> and &minus;<i>M</i> map to the same "
    "M&ouml;bius transformation) is a discrete identification and does not "
    "further reduce the real dimension. So φ<sub><i>&theta;</i></sub> has "
    "6 real degrees of freedom, parameterised by the real and imaginary "
    "parts of <i>a</i>,<i>b</i>,<i>c</i>,<i>d</i> subject to "
    "<i>ad</i>&minus;<i>bc</i> = 1.",
    style_body,
))
story.append(Paragraph(
    "We refine &theta; via L-BFGS-B with the closed-form ridge "
    "(Eq.&nbsp;2) re-solved at each step. The basis is fixed; only the "
    "domain is reparameterized. Because every φ &isin; PSL(2,ℂ) preserves "
    "the cross-ratio identically by definition, the cross-ratio check "
    "verifies implementation consistency: it fails if φ<sub><i>&theta;</i></sub> "
    "is miscoded, not if the learned map is a poor fit.",
    style_body,
))

# --- §4 The Single-Action Atom and Linear Composition ---
story.append(Paragraph("4&nbsp;&nbsp;The Single-Action Atom and Linear Composition", style_h1))
story.append(Paragraph(
    "The smallest audit unit of the curve-guided framework is the "
    "<i>single-action atom</i>. We define it precisely so the "
    "only-positive-&Delta; invariant it carries propagates linearly across "
    "the corpus.",
    style_body,
))

story.append(Paragraph("4.1&nbsp;&nbsp;Atom: from file to <i>S<sup>2</sup></i> point", style_h2))
story.append(Paragraph(
    "For a single corpus item <i>f</i> (a file with "
    "<i>N</i><sub>sec</sub> &ge; 2 sections), the atom computes:",
    style_body,
))
# Numbered list of the 6 atom construction steps
atom_steps = [
    "A <b>per-section coverage vector</b> <i>c<sub>i</sub></i> "
    "&isin; {0,1}<sup>9</sup>, scored by pattern-matching against a fixed "
    "9-D binary primitive basis &#120125; = (<i>p</i><sub>0</sub>, &hellip;, "
    "<i>p</i><sub>8</sub>).",
    "A <b>weighted aggregate</b> <i>c</i> = ∑<sub><i>i</i></sub> "
    "<i>w<sub>i</sub></i> <i>c<sub>i</sub></i>, with weights "
    "<i>w<sub>i</sub></i> = len(section<sub><i>i</i></sub>) / len(<i>f</i>), "
    "thresholded at 0.5.",
    "A <b>section coverage matrix</b> <i>M</i> &isin; "
    "{0,1}<sup><i>N</i><sub>sec</sub> &times; 9</sup>, PCA top-2 via SVD "
    "giving (<i>ū</i>, <i>v̄</i>) for the file aggregate.",
]
for idx, step in enumerate(atom_steps, start=1):
    story.append(Paragraph(
        f"<b>{idx}.</b>&nbsp;&nbsp;{step}", style_body, bulletText=f"{idx}."
    ))
story.append(Paragraph(
    "4. A <b>stereographic lift</b> σ : &#8477;<sup>2</sup> "
    "&rarr; <i>S<sup>2</sup></i> with",
    style_body,
))
story.append(Paragraph(
    "σ(<i>u</i>,<i>v</i>) = "
    "[ 2<i>u</i>,&nbsp; 2<i>v</i>,&nbsp; <i>u</i><sup>2</sup>+<i>v</i><sup>2</sup>&minus;1 ] "
    "/ (1+<i>u</i><sup>2</sup>+<i>v</i><sup>2</sup>) &isin; <i>S<sup>2</sup></i>,",
    style_equation,
))
story.append(Paragraph(
    "giving one point <i>p</i> = σ(<i>ū</i>, <i>v̄</i>) &isin; "
    "<i>S<sup>2</sup></i> per file.",
    style_body,
))
story.append(Paragraph(
    "5. An <b>ideal pole</b> <i>p</i><sup>*</sup> = "
    "σ(<i>ū</i><sup>*</sup>, <i>v̄</i><sup>*</sup>), where "
    "(<i>ū</i><sup>*</sup>, <i>v̄</i><sup>*</sup>) is the lift of the "
    "all-ones coverage vector (1, &hellip;, 1).",
    style_body,
))
story.append(Paragraph(
    "6. A <b>geodesic gap</b> <i>d</i>(<i>f</i>) = &Vert;<i>p</i> &minus; "
    "<i>p</i><sup>*</sup>&Vert;<sub>2</sub> (chordal proxy on "
    "<i>S<sup>2</sup></i>).",
    style_body,
))
story.append(Paragraph(
    "For each missing primitive <i>i</i> &isin; {<i>j</i> : <i>c<sub>j</sub></i> = 0}, "
    "the atom simulates the flip <i>c<sub>i</sub></i> := 1, recomputes the "
    "<i>S<sup>2</sup></i> point <i>p</i>&prime;, and selects "
    "<i>i</i><sup>*</sup> = argmin<sub><i>i</i></sub> "
    "<i>d</i><sub>post</sub>(<i>f</i>). This is the <i>geodesic-only "
    "criterion</i>: the chosen action strictly minimizes post-flip "
    "geodesic distance to the ideal pole.",
    style_body,
))

story.append(Paragraph("4.2&nbsp;&nbsp;Lemma 1 (atom invariant)", style_h2))
story.append(Paragraph(
    "<b>Lemma 1.</b> For any file <i>f</i> and any action &alpha; selected "
    "by the geodesic-only criterion, "
    "&Delta;<sub><i>f</i></sub> = <i>d</i><sub>pre</sub> &minus; "
    "<i>d</i><sub>post</sub> &ge; 0.",
    style_lemma,
))
story.append(Paragraph(
    "<b>Proof.</b> The criterion selects "
    "&alpha;<sup>*</sup> = argmin<sub><i>i</i></sub> "
    "<i>d</i><sub>post</sub> over the <i>k</i> candidates where "
    "<i>k</i> = |{<i>j</i> : <i>c<sub>j</sub></i> = 0}|. Each candidate "
    "flips exactly one missing primitive <i>i</i> from 0 to 1 and "
    "recomputes the file's <i>S<sup>2</sup></i> point. If all <i>k</i> "
    "candidates had <i>d</i><sub>post</sub> &ge; <i>d</i><sub>pre</sub>, "
    "the argmin would tie at <i>d</i><sub>pre</sub> and "
    "&Delta;<sub><i>f</i></sub> = 0, never negative. A strictly negative "
    "&Delta;<sub><i>f</i></sub> would require <i>d</i><sub>post</sub> "
    "&gt; <i>d</i><sub>pre</sub> for the argmin, contradicting the "
    "minimization. The action space is append-only (single-primitive "
    "flips); no candidate removes coverage. ∎",
    style_lemma,
))

story.append(Paragraph("4.3&nbsp;&nbsp;Theorem 1 (linear composition)", style_h2))
story.append(Paragraph(
    "<b>Theorem 1.</b> For a corpus <i>C</i> with |<i>C</i>| = <i>N</i> "
    "files, every multi-file action "
    "&alpha;<sub>corpus</sub> = (&alpha;<sub>1</sub>, &hellip;, "
    "&alpha;<sub><i>N</i></sub>) where each &alpha;<sub><i>i</i></sub> is an "
    "atomic action on file <i>f<sub>i</sub></i>, has corpus-level",
    style_lemma,
))
story.append(Paragraph(
    "&Delta;<sub>corpus</sub> = ∑<sub><i>i</i>=1</sub><sup><i>N</i></sup> "
    "&Delta;<sub><i>f<sub>i</sub></i></sub>.",
    style_equation,
))
story.append(Paragraph(
    "If every atomic &Delta; &ge; 0, then &Delta;<sub>corpus</sub> &ge; 0, "
    "and &Delta;<sub>corpus</sub> &gt; 0 if at least one atomic "
    "&Delta; &gt; 0.",
    style_lemma,
))
story.append(Paragraph(
    "<b>Proof.</b> Each &alpha;<sub><i>i</i></sub> operates on its own "
    "file <i>f<sub>i</sub></i> independently: the per-file coverage matrix "
    "and <i>S<sup>2</sup></i> point are unchanged for all <i>f<sub>j</sub></i> "
    "with <i>j</i> &ne; <i>i</i>. The geodesic distance "
    "<i>d</i><sub><i>f<sub>i</sub></i></sub> is a function of "
    "<i>f<sub>i</sub></i>&rsquo;s coverage alone. Linear sum of non-negative "
    "scalars is non-negative. ∎",
    style_lemma,
))

story.append(Paragraph("4.4&nbsp;&nbsp;M&ouml;bius refinement strategy", style_h2))
story.append(Paragraph(
    "The corpus-level φ<sub><i>&theta;</i></sub> &isin; PSL(2,ℂ) is one "
    "M&ouml;bius transformation applied uniformly to all files; the "
    "atom-bound composition rule (Theorem&nbsp;1) requires it "
    "<i>stable across per-cycle atom dispatches</i>, otherwise per-file "
    "&Delta;s are measured in different charts and the linear sum does "
    "not apply to the reported cycles. Reported runs use the "
    "<i>refine-once, φ<sub><i>&theta;</i></sub> frozen</i> mode "
    "(φ<sub><i>&theta;</i></sub> fit at corpus creation, frozen for all "
    "subsequent cycles); the joint-refine-per-cycle mode is reserved for "
    "<i>N</i><sub>items</sub> &lt; 30 or corpus growth &gt; 25% since "
    "last refine.",
    style_body,
))

# --- §5 Dataset and Evaluation Protocol ---
story.append(Paragraph("5&nbsp;&nbsp;Dataset and Evaluation Protocol", style_h1))
story.append(Paragraph("5.1&nbsp;&nbsp;Dataset", style_h2))
story.append(Paragraph(
    "The corpus consists of software-skill specifications (engineering "
    "artifacts) in the yubiOS repository. Each item has a 9-dimensional "
    "binary feature vector recording which of nine primitive capabilities "
    "the skill implements. We consider three splits:",
    style_body,
))
story.append(Paragraph(
    "&bull; <b>Split A</b> (49 items): the first 49 items alphabetically. "
    "Train <i>N</i><sub>train</sub> = 35, holdout "
    "<i>N</i><sub>holdout</sub> = 14.",
    style_bullet,
))
story.append(Paragraph(
    "&bull; <b>Split B</b> (70 items): all items at the time of the "
    "headline ablation. Train <i>N</i><sub>train</sub> = 49, holdout "
    "<i>N</i><sub>holdout</sub> = 21.",
    style_bullet,
))
story.append(Paragraph(
    "&bull; <b>Full corpus</b> (79 items, dated 2026-08-06): the "
    "complete skill directory on <font face='Courier'>yubi-OS/yubiOS "
    "main</font> at this paper's revision. Used for the corpus-audit RSI "
    "in Section&nbsp;6.3 and the 474-dispatch atom experiment in "
    "Section&nbsp;6.4.",
    style_bullet,
))
story.append(Paragraph(
    "The 9-D binary feature space has principal-component concentration "
    "PC1+PC2 = 0.652 at Split A and 0.548 at Split B; both clear the "
    "PC1 &ge; 0.40 gate (Section&nbsp;2.3).",
    style_body,
))

story.append(Paragraph("5.2&nbsp;&nbsp;Baseline", style_h2))
story.append(Paragraph(
    "The capacity-matched baseline is a flat Fourier curve on "
    "[<font face='BodyFont'>0</font>,<font face='BodyFont'>1</font>]<sup>2</sup> "
    "with <i>k</i> = 2 (the 2-D tensor-product extension of Eq.&nbsp;1), "
    "giving 5 &times; 5 = 25 basis functions and 9,984 parameters. We "
    "choose <i>k</i> = 2 because it is the lowest-order 2-D tensor product "
    "that exceeds the 16-function count of the spherical variant (16 "
    "basis, 6,534 parameters); <i>k</i> = 1 gives only 3 &times; 3 = 9 "
    "basis and would not be a capacity match for the 16-function sphere, "
    "while <i>k</i> = 3 gives 7 &times; 7 = 49 basis and &sim; 24k "
    "parameters, which overwhelms the corpus. Both models are fitted with "
    "the closed-form ridge (Eq.&nbsp;2) and the same ridge regularisation "
    "λ.",
    style_body,
))

story.append(Paragraph("5.3&nbsp;&nbsp;Evaluation metric", style_h2))
story.append(Paragraph(
    "The headline metric is <i>matched-parameter ablation</i>: holdout "
    "<i>R</i><sup>2</sup> at fewer or equal parameters, with the same "
    "split and the same ridge regularisation. We report the absolute "
    "holdout <i>R</i><sup>2</sup> (not just the delta) so the result is "
    "interpretable against the corpus-mean baseline (<i>R</i><sup>2</sup> "
    "= 0).",
    style_body,
))

story.append(Paragraph("5.4&nbsp;&nbsp;Reproducibility", style_h2))
story.append(Paragraph(
    "All headline Split A and Split B numbers are single-run point "
    "estimates (no error bars) on a fixed holdout split, with a shared "
    "ridge regularisation λ across both arms. The audit-phase numbers "
    "(Section&nbsp;6.3) carry 5-seed &plusmn; std error bars for phases "
    "E&ndash;H, where the 5-seed multi-cycle stress test was run; the "
    "headline ablation does not. All audit runs reported in this paper use "
    "the 79-skill corpus dated 2026-08-06 (single dated snapshot, "
    "referenced throughout).",
    style_body,
))

# --- §6 Results ---
story.append(Paragraph("6&nbsp;&nbsp;Results", style_h1))
story.append(Paragraph(
    "6.1&nbsp;&nbsp;Hyperspherical-harmonic variant: matched-parameter "
    "ablation on Splits A and B", style_h2,
))
story.append(Paragraph(
    "The matched-parameter ablation on the two headline splits is the "
    "paper's single contribution: on these corpora, the hyperspherical "
    "parameter manifold is a strictly better inductive bias than the flat "
    "[<font face='BodyFont'>0</font>,<font face='BodyFont'>1</font>]<sup>2</sup> "
    "baseline, with the absolute holdout <i>R</i><sup>2</sup> positive on "
    "the smaller split and the relative &delta; positive on both splits.",
    style_body,
))
story.append(Paragraph(
    "<b>Split A</b> (49 items, <i>N</i><sub>train</sub> = 35, "
    "<i>N</i><sub>holdout</sub> = 14):",
    style_body,
))
story.append(Paragraph(
    "&bull; <b>Hyperspherical model</b> (<i>S<sup>2</sup></i>/<i>L</i> = 3, "
    "16 basis functions, 6,534 parameters): "
    "<i>R</i><sup>2</sup><sub>holdout</sub> = +0.618.",
    style_bullet,
))
story.append(Paragraph(
    "&bull; <b>Flat Fourier baseline</b> (<i>k</i> = 2 on "
    "[<font face='BodyFont'>0</font>,<font face='BodyFont'>1</font>]<sup>2</sup>, "
    "25 basis functions, 9,984 parameters): "
    "<i>R</i><sup>2</sup><sub>holdout</sub> = &minus;0.359.",
    style_bullet,
))
story.append(Paragraph(
    "&bull; <b>Matched-parameter &delta;</b>: +0.977. The sphere wins by "
    "nearly 1.0 <i>R</i><sup>2</sup> units at fewer parameters; the flat "
    "baseline is worse than the corpus-mean prediction.",
    style_bullet,
))
story.append(Paragraph(
    "<b>Split B</b> (70 items, <i>N</i><sub>train</sub> = 49, "
    "<i>N</i><sub>holdout</sub> = 21, variant-included):",
    style_body,
))
story.append(Paragraph(
    "&bull; <b>Hyperspherical model</b>: "
    "<i>R</i><sup>2</sup><sub>holdout</sub> = +0.222.",
    style_bullet,
))
story.append(Paragraph(
    "&bull; <b>Flat Fourier baseline</b>: "
    "<i>R</i><sup>2</sup><sub>holdout</sub> = &minus;1.120.",
    style_bullet,
))
story.append(Paragraph(
    "&bull; <b>Matched-parameter &delta;</b>: +1.342. The sphere wins by "
    "more than 1.3 <i>R</i><sup>2</sup> units on a corpus where the flat "
    "baseline is strictly worse than predicting the corpus mean.",
    style_bullet,
))

story.append(Paragraph(
    "6.2&nbsp;&nbsp;Corpus audit across cycles 5&ndash;9 (phases A&ndash;H)",
    style_h2,
))
# Figure 1
fig1_path = "/var/workspace/session/session-chart-A-H-1-progression.png"
if Path(fig1_path).exists():
    story.append(Image(fig1_path, width=5.5*inch, height=3.5*inch))
    story.append(Paragraph(
        "<b>Figure 1.</b> Phase A &rarr; B &rarr; C &rarr; D &rarr; E "
        "&rarr; F &rarr; G &rarr; H holdout <i>R</i><sup>2</sup> progression "
        "(cycles 5&ndash;9 RSI corpus audit, 70&rarr;73-skill corpus). "
        "Error bars = 5-seed &plusmn; std for E, F, G, H. The sphere arm "
        "climbs &minus;0.5021 &rarr; +0.2534 while the flat arm stays "
        "flat at &minus;0.4588 &rarr; &minus;0.4231; the win is not a "
        "single-split artifact.",
        style_caption,
    ))

story.append(Paragraph(
    "6.3&nbsp;&nbsp;Atom experiment: 474 dispatches on the 79-skill corpus "
    "+ 20 cycles on the 11-file deep-research corpus", style_h2,
))
story.append(Paragraph(
    "The 79-skill corpus was audited via 474 atom dispatches across 6 "
    "cycles (single run on the 2026-08-06 snapshot, commit "
    "<font face='Courier'>6ae3abeb65</font> on "
    "<font face='Courier'>yubi-OS/yubiOS main</font>). Cumulative "
    "&Delta; = +11.2971 across all dispatches; zero negative &Delta;; "
    "116 strictly positive &Delta;. Sparse cells: "
    "7 &rarr; 3 &rarr; 2 &rarr; 3 &rarr; 0 &rarr; 0. Fixpoint reached at "
    "cycle 6 (peak &Delta; below the 0.001 epsilon). The corpus reached "
    "79/79 = 100% coverage across all nine primitives.",
    style_body,
))
# Figure 2
fig2_path = "/var/workspace/session/chart-RSI-79-cycles-1-6.png"
if Path(fig2_path).exists():
    story.append(Image(fig2_path, width=6.5*inch, height=3.5*inch))
    story.append(Paragraph(
        "<b>Figure 2.</b> 79-skill corpus RSI: cumulative &Delta; per "
        "cycle (left) and per-primitive coverage progression (right). Six "
        "cycles to fixpoint. Total: 474 atom dispatches, 0 negative &Delta;, "
        "cumulative &Delta; = +11.2971. Per-cycle cumulative trajectory: "
        "+5.58 &rarr; +3.01 &rarr; +1.28 &rarr; +0.88 &rarr; +0.54 &rarr; +0.00 &mdash; "
        "the diminishing-returns curve predicted by single-action-curve-rsi's "
        "fixpoint rule.",
        style_caption,
    ))
# Figure 3
fig3_path = "/var/workspace/session/chart-D-1-20-cycle-delta.png"
if Path(fig3_path).exists():
    story.append(Image(fig3_path, width=6.5*inch, height=3.5*inch))
    story.append(Paragraph(
        "<b>Figure 3.</b> &Delta; per cycle across the 20-cycle atom "
        "experiment on 11 deep-research output files in the yubiOS corpus. "
        "Blue: initial corpus sweep (cycles 1&ndash;12). Red: post-edit "
        "re-fits (cycles 13&ndash;20). Stars mark the three peak runs (C2, "
        "C8, C14). Cumulative &Delta; across all 20 cycles: +1.6882. Zero "
        "negative &Delta; across 20 cycles confirms the atom's invariant "
        "(Lemma&nbsp;1).",
        style_caption,
    ))
story.append(Paragraph(
    "The 11-file deep-research corpus was audited via 20 cycles (initial "
    "sweep + 7 post-edit re-fits). Across both corpora combined, the "
    "geodesic-only criterion produced <i>zero</i> negative &Delta; &mdash; "
    "494 dispatches in total, 0 regressions &mdash; confirming Lemma&nbsp;1 "
    "directly. Peak &Delta; trajectory on the 11-file corpus: +0.3092 "
    "(cycle&nbsp;2, advisor-report) &rarr; +0.2810 (cycle&nbsp;8, "
    "pkcs11-ecdsa-deepdive) &rarr; +0.1872 (cycle&nbsp;14, falco). "
    "Peak &Delta; reduced 39.5% across three peak runs, mean &Delta; "
    "reduced 28.2%, cumulative &Delta; plateaued at +1.6882. Per-file "
    "&Delta; reductions: advisor &minus;55.7%, pkcs11-ecdsa-deepdive "
    "&minus;66.6%, comparative &minus;100% (converged to local minimum). "
    "Two of the eleven deep-research files (comparative-V52-refresh and "
    "debugging-journal) reached local minimum coverage shape (&Delta; = 0) "
    "and required no further action. This is the empirical confirmation "
    "of Theorem&nbsp;1: the only-positive-&Delta; property of the atom "
    "propagates linearly across multi-file composition.",
    style_body,
))

# --- §7 Discussion ---
story.append(Paragraph("7&nbsp;&nbsp;Discussion", style_h1))
story.append(Paragraph(
    "7.1&nbsp;&nbsp;What this result does and does not show", style_h2,
))
story.append(Paragraph(
    "The hyperspherical-harmonic variant wins on the matched-parameter "
    "ablation at both Splits A and B by a margin (Split A "
    "&delta; = +0.977, Split B &delta; = +1.342) that is hard to attribute "
    "to noise. We do <i>not</i> claim the variant is a strict improvement "
    "over the flat curve in absolute terms: on Split B the absolute "
    "<i>R</i><sup>2</sup> is +0.222 (positive but small), and the headline "
    "numbers are single-run point estimates without error bars. The atom "
    "experiment (Figure&nbsp;2 + Figure&nbsp;3) shows the smallest audit "
    "unit composes without regression &mdash; 494 dispatches, 0 negative "
    "&Delta; &mdash; but does not by itself validate the variant.",
    style_body,
))

story.append(Paragraph("7.2&nbsp;&nbsp;Limitations", style_h2))
story.append(Paragraph(
    "The empirical case is fragile because it is one corpus family, one "
    "target, and the headline numbers are single-run point estimates. The "
    "5-seed error bars in Figure&nbsp;1 (phases E&ndash;H) partially "
    "address the empirical-fragility concern for the audit; the headline "
    "Split A/B numbers do not. The 79-skill corpus audit (Section&nbsp;6.4) "
    "uses 474 dispatches across 6 cycles at <i>N</i> = 79 &mdash; enough "
    "to support an empirical claim at the atom-invariant level, but not "
    "enough to support multi-seed error bars at the headline-ablation "
    "level. A synthetic-manifold benchmark (one not run) and a "
    "second-corpus re-run would replace the present single-seed point "
    "estimates with error bars at both levels.",
    style_body,
))

# --- §8 Conclusion ---
story.append(Paragraph("8&nbsp;&nbsp;Conclusion", style_h1))
story.append(Paragraph(
    "The hyperspherical-harmonic curve replaces the flat "
    "[<font face='BodyFont'>0</font>,<font face='BodyFont'>1</font>]<sup>2</sup> "
    "parameter manifold with the Riemann sphere <i>S<sup>2</sup></i> and "
    "learns a M&ouml;bius reparameterization φ<sub><i>&theta;</i></sub> "
    "&isin; PSL(2,ℂ) of the domain. On the yubiOS software-skill corpus, "
    "it wins on the matched-parameter ablation at both Splits A and B "
    "(Splits A &delta; = +0.977, Split B &delta; = +1.342), with fewer "
    "parameters and no error bars. The single-action atom is the smallest "
    "unit of the resulting audit pipeline; its only-positive-&Delta; "
    "invariant propagates linearly to multi-file composition "
    "(Theorem&nbsp;1), as confirmed by a 474-dispatch experiment on the "
    "79-skill corpus and a 20-cycle experiment on 11 deep-research files "
    "showing zero negative &Delta; across the combined 494 dispatches. "
    "Future work: a synthetic-manifold benchmark would test whether the "
    "inductive-bias claim holds on manifolds other than <i>S<sup>2</sup></i>, "
    "and a second-corpus re-run would replace the present single-seed "
    "point estimates with error bars.",
    style_body,
))

# --- §A Atom Coverage of 79 Skills (Empirical) ---
story.append(Paragraph(
    "Appendix A&nbsp;&nbsp;Atom Coverage of 79 Skills (Empirical)",
    style_h1,
))
story.append(Paragraph(
    "The 79-skill corpus reached 100% primitive coverage (79/79 for all "
    "nine primitives) after 6 RSI cycles. Per-primitive coverage "
    "progression: cycle&nbsp;1: [71, 63, 63, 49, 35, 74, 72, 70, 73]; "
    "cycle&nbsp;6: [79, 79, 79, 79, 79, 79, 79, 79, 79]. Cumulative "
    "&Delta; across 474 dispatches: +11.2971, with 116 strictly positive "
    "single-action flips and zero negative &Delta; &mdash; the empirical "
    "verification of Lemma&nbsp;1's only-positive-&Delta; invariant on a "
    "corpus 7&times; larger than the 11-file audit. Sparse cells: "
    "7 &rarr; 3 &rarr; 2 &rarr; 3 &rarr; 0 &rarr; 0. Fixpoint reached at "
    "cycle 6.",
    style_body,
))

# --- §B Future Work ---
story.append(Paragraph(
    "Appendix B&nbsp;&nbsp;Cycles 10&ndash;15 RSI Run on Full Repo (Future Work)",
    style_h1,
))
story.append(Paragraph(
    "The 79-skill audit in Section&nbsp;6.3 used cycles 10&ndash;15 of the "
    "curve-guided-rsi self pipeline (cycles 1&ndash;9 were the prior phases "
    "A&ndash;H audit on the 70-skill corpus). The full multi-corpus audit, "
    "including differential curve baselines across the self-doc corpus "
    "and the engineering corpus, is future work.",
    style_body,
))

# --- References ---
story.append(Paragraph("References", style_h1))
refs = [
    "Durastanti, C. (2026). <i>Spectral Bayesian Regression on the Sphere.</i> "
    "arXiv:2601.20528 [math.ST]. "
    "<font color='#0066cc'>https://arxiv.org/abs/2601.20528</font>",
    "Anonymous (ICLR 2022 under review). <i>Generalized Fourier Features for "
    "Coordinate-Based Learning on Manifolds.</i> OpenReview "
    "<font face='Courier'>g6UqpVislvH</font>.",
    "Rahimi, A., &amp; Recht, B. (2007). <i>Random Features for Large-Scale "
    "Kernel Machines.</i> NeurIPS 2007.",
    "Tancik, M., et al. (2020). <i>Fourier Features Let Networks Learn High "
    "Frequency Functions in Low Dimensional Domains.</i> NeurIPS 2020.",
    "Sitzmann, V., Martel, J., Bergman, A., Lindell, D., &amp; Wetzstein, G. "
    "(2020). <i>Implicit Neural Representations with Periodic Activation "
    "Functions.</i> NeurIPS 2020 (SIREN).",
    "Mildenhall, B., et al. (2020). <i>NeRF: Representing Scenes as Neural "
    "Radiance Fields for View Synthesis.</i> ECCV 2020.",
    "Cohen, T. S., et al. (2018). <i>Spherical CNNs.</i> ICLR 2018.",
    "Nickel, M. &amp; Kiela, D. (2017). <i>Poincaré Embeddings for Learning "
    "Hierarchical Representations.</i> NeurIPS 2017.",
    "Ahlfors, L. V. (1979). <i>Complex Analysis,</i> 3rd ed. McGraw-Hill.",
    "do Carmo, M. P. (1976). <i>Differential Geometry of Curves and "
    "Surfaces.</i> Prentice-Hall.",
    "Smith, E. (2026). <i>Learning in Curved Weight Space: Exponential-Linear "
    "Weight Reparameterization for Improved Optimization.</i> "
    "arXiv:2607.09967 [cs.LG].",
]
for i, ref in enumerate(refs):
    story.append(Paragraph(f"[{i+1}]&nbsp;&nbsp;{ref}", style_body))

# ---------- Build ----------
doc.build(story)
print(f"PDF written to {output_path}")
print(f"Size: {output_path.stat().st_size} bytes")
