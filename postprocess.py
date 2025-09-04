#!/usr/bin/env python3

import re
from pathlib import Path

def slugify(s: str) -> str:
    """
    Turn a heading into a LaTeX-safe label:
      "Data and info" → "data-and-info"
    """
    s = s.strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^0-9A-Za-z\-]", "", s)
    return s.lower()

# Catch leftover [[...]] after figures & inline-images
LINK_PAT = re.compile(r"\[\[(.*?)\]\]", re.DOTALL)

def make_figure_block(img_path: str, caption: str) -> str:
    """
    Create a LaTeX figure environment from an image path and caption,
    ensuring actual newlines rather than literal '\\n'.
    """
    label = slugify(Path(img_path).stem)
    return fr"""
\begin{{figure}}[h]
    \centering
    \includegraphics[width=\textwidth]{{{img_path}}}
    \caption{{{caption}.}}
    \label{{fig:{label}}}
\end{{figure}}
""".strip() + "\n\n"

def fix_file(path: Path) -> None:
    txt = path.read_text(encoding='utf-8')

    # 1) Un-escape Pandoc’s {[}{[} → [[ and {]}{]} → ]]
    txt = re.sub(r"\{\[\}\{\[", "[[", txt)
    txt = re.sub(r"\{\]\}\{\]\}", "]]", txt)

    # 2) Embedded figures: ![[file.png]] + “Pic …: caption”
    fig_pat = re.compile(
        r"(?m)^!\[\[(?P<path>[^\]]+)\]\]\s*\r?\n"
        r"\s*Pic\s*[^:]+:\s*(?P<cap>.+?)(?:\r?\n|$)",
        re.IGNORECASE
    )
    def fig_repl(m):
        img = m.group('path').strip().strip('{}')
        cap = m.group('cap').strip().rstrip('.')
        return make_figure_block(img, cap)
    txt = fig_pat.sub(fig_repl, txt)

    # 3) Inline images → Figure~\ref{fig:…}
    img_link_pat = re.compile(
        r"(?<!\!)\[\[([^\]\|]+\.(?:png|jpg|jpeg|svg|pdf))\]\]",
        re.IGNORECASE
    )
    def inline_img(m):
        lab = slugify(Path(m.group(1).strip()).stem)
        return f"Figure~\\ref{{fig:{lab}}}"
    txt = img_link_pat.sub(inline_img, txt)

    # 4) Other wikilinks → \hyperref
    def link_repl(m):
        inner = m.group(1).replace(r"\#", "#").replace(r"\textbar", "|").strip()
        if '|' in inner:
            target, alias = map(str.strip, inner.split('|', 1))
        else:
            target, alias = inner, None
        heading = target.split('#')[-1].strip()
        text = alias or heading
        lab  = slugify(heading)
        return f"\\hyperref[{lab}]{{{text}}}"
    txt = LINK_PAT.sub(link_repl, txt)

    # 5) Page-break before each \section
    txt = re.sub(r'(?m)^(\\section\{)', r'\\newpage\n\1', txt)

    # 6) Convert any longtable+caption → floating table + tabularx
    TABLE_PAT = re.compile(
        r'(?ms)\\begin\{longtable\}.*?\\caption\{.*?\}.*?\\end\{longtable\}'
    )
    def table_repl(m):
        block = m.group(0)

        # 6a) extract caption
        cap = re.search(r'\\caption\{(.*?)\}', block, re.DOTALL).group(1).strip()

        # 6b) extract header row between \toprule and \endfirsthead
        hdr_block = re.search(r'\\toprule(.*?)\\endfirsthead', block, re.DOTALL)
        if hdr_block:
            hdr_text = hdr_block.group(1)
        else:
            hdr_text = re.search(r'\\toprule(.*?)\\midrule', block, re.DOTALL).group(1)
        # pull out the textbf cells
        hdrs = re.findall(r'\\textbf\{([^}]+)\}', hdr_text)
        header_line = ' & '.join(f"\\textbf{{{h.strip()}}}" for h in hdrs)

        # 6c) extract data rows after \endlastfoot
        data_block = re.search(r'\\endlastfoot(.*?)\\end\{longtable\}', block, re.DOTALL).group(1)
        # collapse wrapped lines into full rows
        lines = [ln.strip() for ln in data_block.splitlines() if ln.strip()]
        rows = []
        cur = ""
        for ln in lines:
            cur += (" " + ln)
            if ln.endswith(r"\\"):
                rows.append(cur.rstrip("\\").strip())
                cur = ""
        # if leftover
        if cur.strip():
            rows.append(cur.strip())

        # 6d) assemble body: header + midrule + each row
        lines_out = []
        lines_out.append(f"{header_line} \\\\")
        lines_out.append(r"\midrule")
        for row in rows:
            # remove trailing period and ensure no stray \\ 
            row = row.rstrip("\\").rstrip().rstrip(".")
            lines_out.append(f"{row} \\\\")
        body = "\n    ".join(lines_out)

        # 6e) build column spec
        cols = header_line.count('&') + 1
        col_spec = ''.join(['>{\\raggedright\\arraybackslash}X' for _ in range(cols)])

        return (
            "\\begin{table}[htbp]\n"
            "  \\centering\n"
            f"  \\caption{{{cap}}}\n"
            f"  \\begin{{tabularx}}{{\\linewidth}}{{@{{}}{col_spec}@{{}}}}\n"
            "    \\toprule\n"
            f"    {body}\n"
            "    \\bottomrule\n"
            "  \\end{tabularx}\n"
            "\\end{table}\n\n"
        )

    txt = TABLE_PAT.sub(table_repl, txt)

    # 7) Replace any remaining p{…} with X
    txt = re.sub(
        r'>\{\\raggedright\\arraybackslash\}p\{[^}]+\}',
        r'>\\{\\raggedright\\arraybackslash}X',
        txt
    )
    txt = re.sub(r'p\{[^}]+\}', 'X', txt)

    # 8) Repair stray braces in refs, graphics & labels
    txt = re.sub(
        r'\\ref\{fig:\}([^}]+)\}',
        lambda m: f"\\ref{{fig:{m.group(1)}}}",
        txt
    )
    txt = re.sub(
        r'(\\includegraphics\[[^]]+\])\{\}\s*([^}\s]+)\}',
        lambda m: f"{m.group(1)}{{{m.group(2)}}}",
        txt
    )
    txt = re.sub(
        r'\\label\{fig:\}([^}]+)\}',
        lambda m: f"\\label{{fig:{m.group(1)}}}",
        txt
    )

    path.write_text(txt, encoding='utf-8')
    print(f"Processed {path.name}")

def main():
    for tex in sorted(Path('content').glob('*.tex')):
        fix_file(tex)

if __name__ == '__main__':
    main()
