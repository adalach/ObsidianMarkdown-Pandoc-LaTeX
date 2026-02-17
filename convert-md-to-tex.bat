@echo off
REM ------------------------------------------------------------------------------
REM Obsidian Markdown to LaTeX converter
REM Place your .md file and attachments in Markdown\, then run this script.
REM Output is injected into LaTeX\main.tex between the content markers.
REM ------------------------------------------------------------------------------
setlocal enabledelayedexpansion

set "MARKDOWN_DIR=Markdown"
set "TEMPLATE_TEX=LaTeX\main.tex"
set "TMP_TEX=%TEMP%\obsidian-body.tex"

echo Obsidian Markdown -^> LaTeX conversion

REM Check for exactly one Markdown file
set "COUNT=0"
for /f "delims=" %%F in ('dir /b "%MARKDOWN_DIR%\*.md" 2^>nul') do (
    set /a COUNT+=1
    set "MD_FILE=%%F"
)

if !COUNT! EQU 0 (
    echo Error: No Markdown files in %MARKDOWN_DIR%\. Place your .md file there.
    exit /b 1
)

if !COUNT! GTR 1 (
    echo Error: Found multiple .md files. Use exactly one.
    for /f "delims=" %%F in ('dir /b "%MARKDOWN_DIR%\*.md"') do echo   - %%F
    exit /b 1
)

REM Step 1: Copy figures from Markdown\attachments to LaTeX\figures
echo Copying figures to LaTeX\figures\...
python postprocess.py --copy-figures

REM Step 2: Pandoc conversion with Lua filter
echo Converting Markdown to LaTeX...
set "MD_PATH=%MARKDOWN_DIR%\!MD_FILE!"
pandoc "!MD_PATH!" ^
  -f markdown+auto_identifiers ^
  -t latex ^
  --wrap=preserve ^
  --lua-filter=obsidian-labels.lua ^
  --bibliography="LaTeX\bibliography.bib" ^
  --natbib ^
  --metadata=table-environment:ltablex ^
  --metadata=table-width:\textwidth ^
  -o "!TMP_TEX!"

REM Step 3: Post-process and inject into main.tex
echo Injecting content into %TEMPLATE_TEX%
python postprocess.py --input "!TMP_TEX!" --template "%TEMPLATE_TEX%" --markdown "!MD_PATH!"

echo Done. Compile LaTeX\main.tex to produce the PDF.
endlocal
