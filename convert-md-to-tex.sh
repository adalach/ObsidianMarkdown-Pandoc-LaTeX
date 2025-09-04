#!/usr/bin/env bash
set -euo pipefail

echo "Stage 1: Converting Markdown → LaTeX (labels only)"

# Make sure content/ exists
mkdir -p content

for file in obsidian-md/*.md; do
  fname=$(basename "$file" .md)
  slug="${fname// /_}"
  out="content/${slug}.tex"
  echo "$file → $out"

  pandoc "$file" \
    -f markdown+auto_identifiers \
    -t latex \
    --wrap=preserve \
    --lua-filter=obsidian-labels.lua \
    --metadata=table-environment:ltablex \
    --metadata=table-width:\textwidth \
    --bibliography="literature/references.bib" \
    --biblatex \
    -o "$out"
done

echo "Stage 1 complete."