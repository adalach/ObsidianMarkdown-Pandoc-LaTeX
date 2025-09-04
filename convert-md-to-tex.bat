@echo off
setlocal enabledelayedexpansion

REM 1) Ensure output folder
if not exist content mkdir content

echo Stage 1: Pandoc export with Lua labels.
for %%F in (obsidian-md\*.md) do (
    set "fname=%%~nF"
    set "out=!fname: =_!"
    echo %%F → content\!out!.tex
    pandoc "%%F" ^
      -f markdown+auto_identifiers ^
      -t latex ^
      --wrap=preserve ^
      --lua-filter=obsidian-labels.lua ^
      --bibliography="literature\references.bib" ^
      --biblatex ^
      --metadata=table-environment:ltablex ^
      --metadata=table-width:\textwidth ^
      -o "content\!out!.tex"
)

echo Stage 2: Post-processing images, links and tables.
call python postprocess.py

echo All done.
endlocal
