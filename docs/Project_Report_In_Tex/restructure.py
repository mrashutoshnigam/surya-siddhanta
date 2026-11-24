"""Turn pandoc's flat LaTeX of the project report into a structured report-class document."""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()

body = text.split(r"\begin{document}", 1)[1].split(r"\end{document}", 1)[0]

# Main matter starts at chapter 1; references at the end.
main_start = body.index(r"\textbf{1. Introduction}")
ref_start = body.index(r"\textbf{References}")
main = body[main_start:ref_start]
refs = body[ref_start:]

# Abstract body (between \textbf{Abstract} and \textbf{Contents})
abstract = body[body.index(r"\textbf{Abstract}") + len(r"\textbf{Abstract}"):body.index(r"\textbf{Contents}")].strip()


def heading(m):
    num, title = m.group(1), " ".join(m.group(2).split())
    depth = num.count(".")
    cmd = {0: "chapter", 1: "section", 2: "subsection"}[depth]
    return f"\\{cmd}{{{title}}}"


# Headings: \textbf{4.3.1 Title}, \textbf{1. Introduction} (may wrap lines)
main = re.sub(r"\\textbf\{(\d+(?:\.\d+)*)\.?\s+([^{}]+?)\}(?=\n\n)", heading, main)

# Figures: \includegraphics[...alt={...}]{path}\n\nFigure N caption...\n\n
def figure(m):
    path = m.group(1).rsplit("/", 1)[-1]  # images sit beside the .tex
    cap = " ".join(m.group(2).split())
    label = "fig:" + path.rsplit("/", 1)[-1].split(".")[0]
    return ("\\begin{figure}[htbp]\n  \\centering\n"
            f"  \\includegraphics[width=0.95\\linewidth]{{{path}}}\n"
            f"  \\caption{{{cap}}}\n  \\label{{{label}}}\n\\end{{figure}}\n\n")

main = re.sub(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}\n\nFigure \d+ (.+?)\n\n", figure, main, flags=re.S)

# Tables: simplify pandoc's minipage headers into plain bold header rows.
main = re.sub(
    r"\\begin\{minipage\}\[b\]\{\\linewidth\}\\raggedright\n(.+?)\n\\end\{minipage\}",
    lambda m: "\\textbf{" + m.group(1).strip() + "}", main)

# Tidy quote macro
main = main.replace(r"\textquotesingle s", "'s").replace(r"\textquotesingle{}", "'")
main = main.replace(r"\textquotesingle ", "'")

# Let long file paths break across lines
main = main.replace("docs/evaluation/export\\_learning\\_lab.py", "\\path{docs/evaluation/export_learning_lab.py}")
main = main.replace("docs/evaluation/REPRODUCE.md", "\\path{docs/evaluation/REPRODUCE.md}")

# Make the standalone NASA URLs clickable
main = re.sub(r"\((https://[^)\s]+)\)", r"(\\url{\1})", main)

# References -> thebibliography
items = re.findall(r"\{\[\}(\d+)\{\]\}\s+(.+?)(?=\n\n|\Z)", refs, flags=re.S)
bib = "\\begin{thebibliography}{9}\n"
for n, entry in items:
    entry = " ".join(entry.split())
    entry = re.sub(r"doi:(\S+?)\.?$", r"\\doi{\1}.", entry)
    bib += f"\\bibitem{{ref{n}}} {entry}\n\n"
bib += "\\end{thebibliography}\n"

preamble = r"""\documentclass[12pt,a4paper,oneside]{report}

% ---- Fonts (compile with XeLaTeX or LuaLaTeX: the text uses IAST diacritics) ----
\usepackage{fontspec}
\setmainfont{TeX Gyre Termes}
\usepackage{amsmath,amssymb}
% Termes lacks a precomposed m-dot-above (U+1E41); build it from m + combining dot.
\usepackage{newunicodechar}
\newunicodechar{ṁ}{m\char"0307{}}

% ---- Page layout ----
\usepackage[a4paper,left=1.25in,right=1in,top=1in,bottom=1in]{geometry}
\usepackage{setspace}
\onehalfspacing
\usepackage{parskip}
\setlength{\emergencystretch}{3em}

% ---- Headings ----
\usepackage{titlesec}
\titleformat{\chapter}[hang]{\normalfont\LARGE\bfseries}{\thechapter.}{0.6em}{}
\titlespacing*{\chapter}{0pt}{0pt}{1.2em}
\titleformat{\section}{\normalfont\Large\bfseries}{\thesection}{0.8em}{}
\titleformat{\subsection}{\normalfont\large\bfseries}{\thesubsection}{0.8em}{}
\setcounter{secnumdepth}{2}
\setcounter{tocdepth}{2}

% ---- Tables, figures, links ----
\usepackage{longtable,booktabs,array,calc}
\usepackage{graphicx}
\usepackage[font=small,labelfont=bf]{caption}
\usepackage{xcolor}
\usepackage{xurl}
\usepackage[hidelinks,unicode]{hyperref}
\usepackage{bookmark}
\newcommand{\doi}[1]{\href{https://doi.org/#1}{doi:#1}}

% ---- Header/footer ----
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}}

% ---- Report metadata ----
\newcommand{\reporttitle}{Computational Implementation of the Surya Siddhanta Across Fourteen Chapters}
\newcommand{\authorname}{Ashutosh Nigam}
\newcommand{\rollno}{M25AI2006}
\newcommand{\degree}{M.Tech.}
\newcommand{\supervisor}{Dr.\ Dinesh Mohan Joshi}
\newcommand{\institute}{Indian Institute of Technology Jodhpur}
\newcommand{\department}{Department of Computer Science and Engineering}
\newcommand{\submissiondate}{November 2026}

\hypersetup{pdftitle={\reporttitle},pdfauthor={\authorname}}

\begin{document}

\pagenumbering{roman}

% ================= Abstract =================
\chapter*{Abstract}
\addcontentsline{toc}{chapter}{Abstract}

"""

toc = r"""

% ================= Contents =================
\tableofcontents

\clearpage
\pagenumbering{arabic}

"""

# Give the two-column tables captions so they appear in the list of tables.
captions = iter(["Learning paths and their implemented experiments",
                 "Interface validation checks and their evidence"])
def captioned(m):
    cap = next(captions)
    head = m.group(2)
    return (m.group(1) + "\\caption{" + cap + "}\\\\\n" + head + "\\endfirsthead\n"
            + "\\caption[]{" + cap + " (continued)}\\\\\n" + head + "\\endhead\n")

main = re.sub(r"(\\begin\{longtable\}\[\]\{@\{\}.*?@\{\}\}\n)(.*?)\\endhead\n",
              captioned, main, flags=re.S)

out = preamble + abstract + toc + main.strip() + "\n\n" + \
      "\\cleardoublepage\n\\phantomsection\n\\addcontentsline{toc}{chapter}{References}\n" + \
      "\\renewcommand{\\bibname}{References}\n" + bib + "\n\\end{document}\n"
open(dst, "w", encoding="utf-8").write(out)
print("chapters", out.count("\\chapter{"), "sections", out.count("\\section{"),
      "subsections", out.count("\\subsection{"), "figures", out.count("\\begin{figure}"),
      "bibitems", out.count("\\bibitem"))
