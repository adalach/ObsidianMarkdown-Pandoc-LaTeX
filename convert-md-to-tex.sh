#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# Obsidian Markdown to LaTeX converter
# Place your .md file and attachments in Markdown/, then run this script.
# Output is injected into LaTeX/main.tex between the content markers.
# ------------------------------------------------------------------------------
set -euo pipefail

MARKDOWN_DIR="Markdown"
TEMPLATE_TEX="LaTeX/main.tex"

echo "Obsidian Markdown -> LaTeX conversion"

# Check for exactly one Markdown file
shopt -s nullglob
md_files=("${MARKDOWN_DIR}"/*.md)

if [ ${#md_files[@]} -eq 0 ]; then
  echo "Error: No Markdown files in ${MARKDOWN_DIR}/. Place your .md file there."
  exit 1
fi

if [ ${#md_files[@]} -gt 1 ]; then
  echo "Error: Found multiple .md files. Use exactly one:"
  printf '  - %s\n' "${md_files[@]}"
  exit 1
fi

# Use a temp file; no build/ directory left in the project
TMP_TEX=$(mktemp -t obsidian-body.XXXXXX.tex)
trap 'rm -f "${TMP_TEX}"' EXIT

# Step 1: Copy figures from Markdown/attachments and Markdown/ to LaTeX/figures
echo "Copying figures to LaTeX/figures/..."
python3 postprocess.py --copy-figures

# Step 2: Pandoc conversion with Lua filter for labels
echo "Converting Markdown to LaTeX..."
pandoc "${md_files[0]}" \
  -f markdown+auto_identifiers \
  -t latex \
  --wrap=preserve \
  --lua-filter=obsidian-labels.lua \
  --metadata=table-environment:ltablex \
  --metadata=table-width:\textwidth \
  --bibliography="LaTeX/bibliography.bib" \
  --natbib \
  -o "${TMP_TEX}"

# Step 3: Post-process and inject into main.tex
echo "Injecting content into ${TEMPLATE_TEX}"
python3 postprocess.py --input "${TMP_TEX}" --template "${TEMPLATE_TEX}" --markdown "${md_files[0]}"

echo "Done. Compile LaTeX/main.tex to produce the PDF."
