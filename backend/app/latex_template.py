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


# Jake Gutierrez's resume template (MIT, https://github.com/sb2nov/resume).
# The preamble and custom macros are used verbatim; render_cv fills them with
# the model's escaped content. Compiles with pdfLaTeX in a standard TeX distro
# (Overleaf default). glyphtounicode + \pdfgentounicode=1 make the PDF ATS-parsable.
_PREAMBLE = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\pdfgentounicode=1

\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}
"""


def render_cv(content: dict) -> str:
    """Assemble a full .tex document from the model's structured content."""
    name = tex_escape(content.get("name") or "Your Name")
    headline = tex_escape(content.get("headline"))
    # A bare "|" renders as an em-dash in LaTeX text mode; the template uses $|$
    # as the contact separator, so switch pipes to math-mode bars after escaping.
    contact = tex_escape(content.get("contact")).replace("|", "$|$")

    header = [f"    \\textbf{{\\Huge \\scshape {name}}} \\\\ \\vspace{{1pt}}"]
    if contact:
        header.append(f"    \\small {contact}")
    if headline:
        header.append(f" \\\\ \\vspace{{2pt}}\n    \\textit{{{headline}}}")
    header_block = "\\begin{center}\n" + "\n".join(header) + "\n\\end{center}\n"

    body_parts: List[str] = []

    summary = content.get("summary")
    if summary:
        body_parts.append(
            "\\section{Summary}\n" + tex_escape(summary) + "\n"
        )

    experience = content.get("experience") or []
    exp_chunks: List[str] = []
    for entry in experience:
        project = tex_escape(entry.get("project"))
        bullets = [b for b in (entry.get("bullets") or []) if b]
        if not bullets:
            continue
        heading = (
            f"      \\resumeProjectHeading\n"
            f"          {{\\textbf{{{project}}}}}{{}}\n" if project else ""
        )
        items = "\n".join(
            f"            \\resumeItem{{{tex_escape(b)}}}" for b in bullets
        )
        exp_chunks.append(
            f"{heading}"
            f"          \\resumeItemListStart\n{items}\n          \\resumeItemListEnd"
        )
    if exp_chunks:
        body_parts.append(
            "\\section{Experience}\n"
            "  \\resumeSubHeadingListStart\n"
            + "\n".join(exp_chunks)
            + "\n  \\resumeSubHeadingListEnd\n"
        )

    skills = [tex_escape(s) for s in (content.get("skills") or []) if s]
    if skills:
        body_parts.append(
            "\\section{Technical Skills}\n"
            " \\begin{itemize}[leftmargin=0.15in, label={}]\n"
            "    \\small{\\item{\n"
            "     " + ", ".join(skills) + "\n"
            "    }}\n"
            " \\end{itemize}\n"
        )

    body = "\n".join(p for p in body_parts if p)
    return f"{_PREAMBLE}\n\\begin{{document}}\n{header_block}\n{body}\n\\end{{document}}\n"
