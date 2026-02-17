#!/usr/bin/env python3
"""
Post-process Pandoc LaTeX output from Obsidian Markdown.
Converts Obsidian syntax (![[images]], [[wikilinks]]) to LaTeX, injects content
into the template, and ensures figures are referenced from LaTeX/figures/.
"""

import argparse
import re
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

# -----------------------------------------------------------------------------
# Injection markers: content is placed between these in main.tex
# -----------------------------------------------------------------------------
MARKER_START = "% === BEGIN MARKDOWN CONTENT ==="
MARKER_END = "% === END MARKDOWN CONTENT ==="

# Image paths: where to look for source images, and where they end up in LaTeX
IMAGE_DEFAULT_ROOT = "figures"
IMAGE_ROOTS = (
    "figures",
    "LaTeX/figures",
    "Markdown/attachments",
    "Markdown",
)
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".svg", ".pdf")

# Unicode arrows that can break LaTeX compilation depending on engine/fonts.
# Use \ensuremath so replacements work both in text and in existing math.
UNICODE_ARROW_TO_LATEX = {
    "→": r"\ensuremath{\to}",
    "←": r"\ensuremath{\leftarrow}",
    "↔": r"\ensuremath{\leftrightarrow}",
    "⇒": r"\ensuremath{\Rightarrow}",
    "⇐": r"\ensuremath{\Leftarrow}",
    "⇔": r"\ensuremath{\Leftrightarrow}",
    "↦": r"\ensuremath{\mapsto}",
    "⟶": r"\ensuremath{\longrightarrow}",
    "⟵": r"\ensuremath{\longleftarrow}",
    "⟷": r"\ensuremath{\longleftrightarrow}",
    "⟹": r"\ensuremath{\Longrightarrow}",
    "⟸": r"\ensuremath{\Longleftarrow}",
    "⟺": r"\ensuremath{\Longleftrightarrow}",
}


def slugify(s: str) -> str:
    """
    Turn a heading into a LaTeX-safe label:
      "Data and info" -> "data-and-info"
    """
    s = s.strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^0-9A-Za-z\-]", "", s)
    return s.lower()


def normalize_image_path(img_path: str) -> str:
    """
    Resolve an image path from Markdown/attachments or Markdown to the
    LaTeX output path. All local figures are referenced as figures/<name>.
    """
    path = img_path.strip().strip("{}")
    path = path.replace(r"\ ", " ").replace(r"\_", "_")
    path = path.replace("\\", "/")
    if path.startswith(("http://", "https://")):
        return path
    if path.startswith("/") or re.match(r"^[A-Za-z]:/", path):
        return path

    basename = Path(path).name
    candidates = [f"{root}/{path}" for root in IMAGE_ROOTS]
    if basename != path:
        candidates.extend([f"{root}/{basename}" for root in IMAGE_ROOTS])

    for cand in candidates:
        if Path(cand).exists():
            # Always output figures/<name> so LaTeX finds them in LaTeX/figures/
            return f"{IMAGE_DEFAULT_ROOT}/{basename}"
    return f"{IMAGE_DEFAULT_ROOT}/{path}"


# Catch leftover [[...]] after figures & inline-images
LINK_PAT = re.compile(r"\[\[(.*?)\]\]", re.DOTALL)

CAPTION_LINE_PAT = re.compile(
    r"(?i)^(?:Fig(?:ure)?|Pic|Caption)\.?\s*[^:\n]*[:\-]\s*(.+)$"
)


def tex_image_path(img_path: str) -> str:
    path = normalize_image_path(img_path)
    path = path.replace("_", r"\_")
    return path.replace(" ", r"\ ")


def path_stem(img_path: str) -> str:
    raw = img_path.replace(r"\ ", " ")
    return Path(raw).stem


def caption_from_filename(img_path: str) -> str:
    stem = path_stem(img_path)
    caption = stem.replace("_", " ").replace("-", " ").strip()
    if not caption:
        return "Figure"
    return caption[:1].upper() + caption[1:]


def replace_unicode_arrows(txt: str) -> str:
    if not txt:
        return txt
    if not any(ch in txt for ch in UNICODE_ARROW_TO_LATEX.keys()):
        return txt
    pat = re.compile("|".join(map(re.escape, UNICODE_ARROW_TO_LATEX.keys())))
    return pat.sub(lambda m: UNICODE_ARROW_TO_LATEX[m.group(0)], txt)


def make_figure_block(img_path: str, caption: str) -> str:
    """
    Create a LaTeX figure environment from an image path and caption,
    ensuring actual newlines rather than literal '\\n'.
    """
    label = slugify(path_stem(img_path))
    return (
        "\n"
        "\\begin{figure}[htbp]\n"
        "    \\centering\n"
        f"    \\includegraphics[width=\\columnwidth]{{{img_path}}}\n"
        f"    \\caption{{{caption}.}}\n"
        f"    \\label{{fig:{label}}}\n"
        "\\end{figure}\n"
    ).strip() + "\n\n"


def process_text(txt: str, file_slug: Optional[str] = None) -> str:
    # 1) Un-escape Pandoc's {[}{[} -> [[ and {]}{]} -> ]]
    txt = re.sub(r"\{\[\}\{\[\}", "[[", txt)
    txt = re.sub(r"\{\]\}\{\]\}", "]]", txt)

    # 2) Embedded figures: ![[file.png]] + "Pic ...: caption"
    fig_pat = re.compile(
        r"(?m)^!\[\[(?P<path>[^\]]+)\]\]\s*\r?\n"
        r"\s*(?P<capline>(?:Fig(?:ure)?|Pic|Caption)[^\n]*[:\-][^\n]*)(?:\r?\n|$)",
        re.IGNORECASE,
    )

    def fig_repl(m):
        img_raw = m.group("path")
        capline = m.group("capline").strip()
        cap_match = CAPTION_LINE_PAT.match(capline)
        if not cap_match:
            return m.group(0)
        cap = cap_match.group(1).strip().rstrip(".")
        img = tex_image_path(img_raw)
        return make_figure_block(img, cap)

    txt = fig_pat.sub(fig_repl, txt)

    # 2b) Embedded figures without explicit captions
    fig_nocap_pat = re.compile(
        r"(?m)^!\[\[(?P<path>[^\]]+)\]\]\s*(?:\r?\n|$)"
    )

    def fig_nocap_repl(m):
        img_raw = m.group("path")
        if not img_raw.lower().endswith(IMAGE_EXTS):
            return m.group(0)
        img = tex_image_path(img_raw)
        cap = caption_from_filename(img_raw)
        return make_figure_block(img, cap)

    txt = fig_nocap_pat.sub(fig_nocap_repl, txt)

    # 3) Inline images -> Figure~\\ref{fig:...}
    img_link_pat = re.compile(
        r"(?<!\!)\[\[([^\]\|]+\.(?:png|jpg|jpeg|svg|pdf))\]\]",
        re.IGNORECASE,
    )

    def inline_img(m):
        lab = slugify(Path(m.group(1).strip()).stem)
        return f"Figure~\\ref{{fig:{lab}}}"

    txt = img_link_pat.sub(inline_img, txt)

    # 4) Other wikilinks -> \\hyperref
    def link_repl(m):
        inner = m.group(1).replace(r"\#", "#").replace(r"\textbar", "|").strip()
        if "|" in inner:
            target, alias = map(str.strip, inner.split("|", 1))
        else:
            target, alias = inner, None
        if "#" in target:
            note, heading = map(str.strip, target.split("#", 1))
        else:
            note, heading = target.strip(), ""
        if heading:
            text = alias or heading
            if note:
                lab = f"{slugify(note)}--{slugify(heading)}"
            else:
                # [[#Heading]] same-file ref: use file_slug--heading if available
                lab = (
                    f"{file_slug}--{slugify(heading)}" if file_slug else slugify(heading)
                )
        else:
            text = alias or note
            lab = slugify(note)
        return f"\\hyperref[{lab}]{{{text}}}"

    txt = LINK_PAT.sub(link_repl, txt)

    # 4b) Rewrite heading labels to include file slug for cross-references
    if file_slug:

        def rewrite_heading_label(m: re.Match) -> str:
            lab = m.group(1)
            if lab.startswith("fig:") or "--" in lab:
                return m.group(0)
            return f"\\label{{{file_slug}--{lab}}}"

        txt = re.sub(r"\\label\{([^}]+)\}", rewrite_heading_label, txt)

    # 4c) Remove \tightlist for normal LaTeX list spacing
    txt = re.sub(r"\n\\tightlist\n?", "\n", txt)

    # 4d) Add vertical space after lists for breathing room
    txt = re.sub(r"(\\end\{itemize\})\s*\n", r"\1\n\\bigskip\n", txt)
    txt = re.sub(r"(\\end\{enumerate\})\s*\n", r"\1\n\\bigskip\n", txt)

    # 5) (No page-break before \\section - user prefers continuous flow)

    # 5b) Fix literal Markdown headings that slipped through
    txt = re.sub(r"(?m)^\\#\\#\\#\\#\s+(.+)$", r"\\paragraph{\1}", txt)

    # 6) Convert any longtable -> floating table + tabularx
    # "Table slug: caption" above table → caption before tabularx; below → caption after tabularx
    TABLE_CAP_ABOVE = re.compile(
        r"(?:(?:^|\n)(Table ([a-zA-Z0-9_-]+): ([^\n]+))(?:\n\s*)+)?"
        r"(\\begin\{longtable\}.*?\\end\{longtable\})",
        re.DOTALL,
    )
    TABLE_CAP_BELOW = re.compile(
        r"(\\begin\{longtable\}.*?\\end\{longtable\})"
        r"(?:\n\s*)+(?:^|\n)(Table ([a-zA-Z0-9_-]+): ([^\n]+))",
        re.DOTALL,
    )
    table_slugs: List[str] = []

    def extract_braced(text: str, start: int) -> Tuple[str, int]:
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            i += 1
        return text[start : i - 1], i

    def extract_caption_and_label(block: str) -> Tuple[Optional[str], Optional[str]]:
        cap = None
        label = None

        cap_idx = block.find("\\caption{")
        if cap_idx != -1:
            cap_text, end_idx = extract_braced(block, cap_idx + len("\\caption{"))
            cap = cap_text.strip()

        label_match = re.search(r"\\label\{([^}]+)\}", block)
        if label_match:
            label = label_match.group(1).strip()
            if cap:
                cap = re.sub(r"\\label\{[^}]+\}", "", cap).strip()

        return cap or None, label or None

    def normalize_col_spec(spec: str) -> str:
        spec = " ".join(spec.split())
        out = []
        i = 0
        while i < len(spec):
            if spec[i] in ("p", "m", "b") and i + 1 < len(spec) and spec[i + 1] == "{":
                i += 2
                depth = 1
                while i < len(spec) and depth > 0:
                    if spec[i] == "{":
                        depth += 1
                    elif spec[i] == "}":
                        depth -= 1
                    i += 1
                out.append("X")
                continue
            out.append(spec[i])
            i += 1
        return "".join(out)

    def build_table(block: str, cap: Optional[str], label: Optional[str], caption_above: bool) -> str:
        begin_idx = block.find("\\begin{longtable}")
        if begin_idx == -1:
            return block
        scan_idx = begin_idx + len("\\begin{longtable}")
        if scan_idx < len(block) and block[scan_idx] == "[":
            end_opt = block.find("]", scan_idx)
            if end_opt != -1:
                scan_idx = end_opt + 1
        brace_start = block.find("{", scan_idx)
        if brace_start == -1:
            return block
        col_spec_raw, _ = extract_braced(block, brace_start + 1)
        col_spec = normalize_col_spec(col_spec_raw).strip()
        prefix = "" if col_spec.startswith("@{}") else "@{}"
        suffix = "" if col_spec.endswith("@{}") else "@{}"

        header_block = ""
        header_match = re.search(r"\\toprule.*?\\endfirsthead", block, re.DOTALL)
        if header_match:
            header_block = header_match.group(0).replace("\\endfirsthead", "").strip()
        else:
            top_match = re.search(r"\\toprule.*?\\midrule", block, re.DOTALL)
            if top_match:
                header_block = top_match.group(0).strip()

        data_match = re.search(
            r"\\endlastfoot(.*?)\\end\{longtable\}", block, re.DOTALL
        )
        if not data_match:
            data_match = re.search(r"\\endhead(.*?)\\end\{longtable\}", block, re.DOTALL)
        if data_match:
            data_block = data_match.group(1).strip()
        else:
            data_block = ""

        body_parts = [part for part in (header_block, data_block) if part]
        body = "\n".join(body_parts).strip()
        if body and "\\bottomrule" not in body:
            body = f"{body}\n\\bottomrule"

        lines = ["", "\\begin{table}[htbp]", "  \\centering"]
        if caption_above and cap:
            lines.append(f"  \\caption{{{cap}}}")
            if label:
                lines.append(f"  \\label{{{label}}}")
        lines.append(f"  \\begin{{tabularx}}{{\\linewidth}}{{{prefix}{col_spec}{suffix}}}")
        if body:
            lines.append(f"    {body}")
        lines.append("  \\end{tabularx}")
        if not caption_above and cap:
            lines.append(f"  \\caption{{{cap}}}")
            if label:
                lines.append(f"  \\label{{{label}}}")
        lines.append("\\end{table}\n")
        return "\n".join(lines)

    def table_repl_above(m):
        cap_slug, cap_text = m.group(2), m.group(3)
        block = m.group(4)
        cap, label = extract_caption_and_label(block)
        if cap_slug and cap_text:
            table_slugs.append(cap_slug)
            label = f"tbl:{slugify(cap_slug)}"
            cap = cap_text.strip().rstrip(".")
        return build_table(block, cap, label, caption_above=True)

    def table_repl_below(m):
        block = m.group(1)
        cap_slug, cap_text = m.group(3), m.group(4)
        table_slugs.append(cap_slug)
        label = f"tbl:{slugify(cap_slug)}"
        cap = cap_text.strip().rstrip(".")
        return build_table(block, cap, label, caption_above=False)

    # Process caption-below first (more specific), then caption-above
    txt = TABLE_CAP_BELOW.sub(table_repl_below, txt)
    txt = TABLE_CAP_ABOVE.sub(table_repl_above, txt)

    # 6b) Replace "Table slug" in text with Table~\ref{tbl:slug} for known table slugs
    for cap_slug in table_slugs:
        lab = slugify(cap_slug)
        # Match "Table slug" as a word (not inside other refs/labels)
        pat = re.compile(r"(?<![\\{])\bTable " + re.escape(cap_slug) + r"\b")
        txt = pat.sub(f"Table~\\\\ref{{tbl:{lab}}}", txt)

    # 7) Repair stray braces in refs, graphics & labels
    txt = re.sub(
        r"\\ref\{fig:\}([^}]+)\}",
        lambda m: f"\\ref{{fig:{m.group(1)}}}",
        txt,
    )
    txt = re.sub(
        r"(\\includegraphics\[[^]]+\])\{\}\s*([^}\s]+)\}",
        lambda m: f"{m.group(1)}{{{m.group(2)}}}",
        txt,
    )
    txt = re.sub(
        r"\\label\{fig:\}([^}]+)\}",
        lambda m: f"\\label{{fig:{m.group(1)}}}",
        txt,
    )

    # 8) Replace unicode arrows with LaTeX-safe math macros
    txt = replace_unicode_arrows(txt)

    # 9) Convert display math \[ ... \] to \begin{equation} ... \end{equation} for numbering
    txt = re.sub(r"\\\[(.*?)\\]", r"\\begin{equation}\1\\end{equation}", txt, flags=re.DOTALL)

    return txt


def inject_body(template_text: str, body_text: str) -> str:
    if MARKER_START not in template_text or MARKER_END not in template_text:
        raise ValueError(
            "Template is missing injection markers: "
            f"{MARKER_START} / {MARKER_END}"
        )
    before, rest = template_text.split(MARKER_START, 1)
    _, after = rest.split(MARKER_END, 1)
    body = body_text.rstrip() + "\n"
    return f"{before}{MARKER_START}\n{body}{MARKER_END}{after}"


def fix_file(path: Path) -> None:
    txt = path.read_text(encoding="utf-8")
    txt = process_text(txt)
    path.write_text(txt, encoding="utf-8")
    print(f"Processed {path.name}")


def copy_figures_to_latex(markdown_dir: str = "Markdown", latex_figures: str = "LaTeX/figures") -> int:
    """
    Copy image files from Markdown/attachments and Markdown/ to LaTeX/figures.
    Overwrites existing files. Returns the number of files copied.
    """
    dest = Path(latex_figures)
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for root_name in ("attachments", ""):
        src_dir = Path(markdown_dir) / root_name if root_name else Path(markdown_dir)
        if not src_dir.exists():
            continue
        for ext in IMAGE_EXTS:
            for f in src_dir.glob(f"*{ext}"):
                if f.is_file():
                    dest_file = dest / f.name
                    shutil.copy2(f, dest_file)
                    count += 1
                    print(f"  Copied {f.relative_to(markdown_dir)} -> {latex_figures}/")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post-process Pandoc LaTeX output for Obsidian Markdown conversion."
    )
    parser.add_argument("--input", help="Path to the Pandoc-generated .tex file.")
    parser.add_argument("--output", help="Where to write the processed output.")
    parser.add_argument(
        "--template",
        help="Template .tex file to inject processed content into.",
    )
    parser.add_argument(
        "--copy-figures",
        action="store_true",
        help="Copy images from Markdown/ to LaTeX/figures before processing.",
    )
    parser.add_argument(
        "--markdown",
        help="Path to the source .md file (for resolving [[#Heading]] same-file refs).",
    )
    args = parser.parse_args()

    if args.copy_figures:
        n = copy_figures_to_latex()
        if n:
            print(f"Copied {n} figure(s) to LaTeX/figures/")
        else:
            print("No figures found in Markdown/ or Markdown/attachments/")

    file_slug = None
    if args.markdown:
        stem = Path(args.markdown).stem
        file_slug = slugify(stem)

    if args.input:
        txt = Path(args.input).read_text(encoding="utf-8")
        txt = process_text(txt, file_slug=file_slug)
        if args.template:
            template_text = Path(args.template).read_text(encoding="utf-8")
            merged = inject_body(template_text, txt)
            out_path = Path(args.output) if args.output else Path(args.template)
            out_path.write_text(merged, encoding="utf-8")
            print(f"Updated {out_path}")
        else:
            out_path = Path(args.output) if args.output else Path(args.input)
            out_path.write_text(txt, encoding="utf-8")
            print(f"Processed {out_path.name}")
        return

    for tex in sorted(Path("content").glob("*.tex")):
        fix_file(tex)


if __name__ == "__main__":
    main()
