"""Render tailored CV content into a curated, compile-safe LaTeX document.

The LLM only ever produces *content* (plain strings). This module is the single
place that emits LaTeX, so:
  * every user/model string is escaped (no macro injection, no broken compiles),
  * the preamble uses only packages present in a standard TeX distribution
    (works in Overleaf and, later, Tectonic without extra downloads).
"""
import re
from typing import List

# A single-pass substitution: each special char maps to its LaTeX-safe form. Doing
# this in one regex pass (rather than sequential str.replace) is essential — otherwise
# braces inserted by \textbackslash{} would be re-escaped into broken output.
_ESCAPE_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_ESCAPE_RE = re.compile("[" + re.escape("".join(_ESCAPE_MAP)) + "]")


def tex_escape(value) -> str:
    if value is None:
        return ""
    return _ESCAPE_RE.sub(lambda m: _ESCAPE_MAP[m.group()], str(value))


_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[margin=1.6cm]{geometry}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}

\setlist[itemize]{leftmargin=1.2em, itemsep=2pt, topsep=2pt}
\titleformat{\section}{\large\bfseries\scshape}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{10pt}{6pt}
\pagestyle{empty}
\setlength{\parindent}{0pt}
"""


def _section(title: str, body: str) -> str:
    if not body.strip():
        return ""
    return f"\\section{{{tex_escape(title)}}}\n{body}\n"


def render_cv(content: dict) -> str:
    """Assemble a full .tex document from the model's structured content."""
    name = tex_escape(content.get("name") or "Your Name")
    headline = tex_escape(content.get("headline"))
    contact = tex_escape(content.get("contact"))

    header = [f"{{\\huge\\bfseries {name}}}\\\\[2pt]"]
    if headline:
        header.append(f"{{\\itshape {headline}}}\\\\[2pt]")
    if contact:
        header.append(f"{contact}\\\\")
    header_block = "\\begin{center}\n" + "\n".join(header) + "\n\\end{center}\n"

    body_parts: List[str] = []

    summary = content.get("summary")
    if summary:
        body_parts.append(_section("Summary", tex_escape(summary)))

    experience = content.get("experience") or []
    exp_chunks: List[str] = []
    for entry in experience:
        project = tex_escape(entry.get("project"))
        bullets = [b for b in (entry.get("bullets") or []) if b]
        if not bullets:
            continue
        heading = f"\\textbf{{{project}}}\\\\[2pt]\n" if project else ""
        items = "\n".join(f"  \\item {tex_escape(b)}" for b in bullets)
        exp_chunks.append(f"{heading}\\begin{{itemize}}\n{items}\n\\end{{itemize}}")
    body_parts.append(_section("Experience", "\n\\vspace{4pt}\n".join(exp_chunks)))

    skills = [tex_escape(s) for s in (content.get("skills") or []) if s]
    if skills:
        body_parts.append(_section("Skills", ", ".join(skills)))

    body = "\n".join(p for p in body_parts if p)
    return f"{_PREAMBLE}\n\\begin{{document}}\n{header_block}\n{body}\n\\end{{document}}\n"
