
# Shortcut:

### Default directory structure:
The file structure I use is like below. To change it, edit the corresponding files, as described later.
```
Project/
├─ convert-md-to-tex.bat           # Windows runner (Pandoc + postprocess)
├─ convert-md-to-tex.sh            # macOS/Linux runner (Pandoc)
├─ obsidian-labels.lua             # Lua filter used by Pandoc
├─ postprocess.py                  # Stage 2 cleanup: images/links/tables tweaks

├─ obsidian-md/                    # INPUT: Obsidian Markdown notes
│  ├─ Note 01.md
│  ├─ Note 02.md
│  └─ attachments/                 # Images referenced by notes
│     ├─ fig1.png
│     └─ diagram.svg
├─ literature/                     # Bibliography etc.
│  └─ references.bib
├─ content/                        # OUTPUT: generated .tex files
   └─ (auto-populated)
```


### On Windows:
The script is run by clicking an Obsidian link inside of a note, for example:
```
[Convert Markdown to LaTeX with Postprocessing](file:///C:/Obsidian%20Vault/Project/convert-md-to-tex.bat)
```
The preconfigured bat file calls Pandoc with Lua filter to process all the Markdown scripts in a given folder and converts them to Latex, then calls a Python script for additional processing.

#### On Mac:
The easiest way to execute a file from Obsidian on Mac is to use `Shell commands` community plugin. Here the shell script (Pandoc+Lua) must be executed separately than the Python script.
In `Shell commands` community plugin create two links to the files:
`Project/convert-md-to-tex.sh`, 
`python3 "Project/postprocess.py"`, 
Careful: Check the plugin's settings, especially the "Working Directory".

In terminal, to make files executable:
```
chmod +x convert-md-to-tex.sh postprocess.py obsidian-labels.lua
```

```
[Convert Markdown to LaTeX](obsidian://shell-commands/?vault=Obsidian%20Vault&execute=XXXXX)
[Postprocess in Python](obsidian://shell-commands/?vault=Obsidian%20Vault&execute=XXXXX)
```
Replace the links with the address from the `Shell commands` community plugin.

# Requirements

- **Pandoc** 
- **Python**: for post-processing LaTeX output (`postprocess.py`)
- Obsidian Community plugins: 
	- Pandoc Plugin - for format conversion
	- Pandoc Reference List - for handling bibliography (here linked with Zotero)
	- Shell commands (for MacOS) - for running the scripts from the Obsidian note
- **Obsidian notes**: Markdown with Obsidian-specific syntax.
- **Bibliography file** (if you cite): `literature/references.bib` (BibTeX format).
	- The citations in Obsidian are handled by Pandoc and are converted as follows:
		- [@authorTitleTitle2025] -> \autocite{authorTitleTitle2025}
		- @authorTitleTitle2025 ->  \textcite{authorTitleTitle2025}
	- Recommended: using Zotero for references and `Zotero Integration` Obsidian plugin.

### LaTeX Packages Expected by the Output
Your LaTeX preamble/template should load at least:
- `graphicx` (images)
- `hyperref` (links)
- `booktabs` (formal tables)
- `tabularx` (stretchy X columns)
- `float` (only if you use `[H]` placement)
- `ltablex` (only if you choose to keep multipage tables with X columns)
- `biblatex` (if citing; requires `biber`)


## Converting Obsidian Markdown Notes to LaTeX

These scripts (`convert-md-to-tex.bat` for Windows and `convert-md-to-tex.sh` for macOS/Linux) automate the process of converting Markdown notes from **Obsidian** into **LaTeX files** using **Pandoc**. They are designed to handle references, internal links, images, and tables in a consistent way.
We have a **two‐stage pipeline**:

1. **Stage 1** (`convert-md-to-tex.sh` / `.bat` + `obsidian-labels.lua`):  
   - **Runs Pandoc** on each `.md` in `obsidian-md/`  
	   - Pandoc is a great tool for converting between markup formats.
	   - Mathematical formulas are nicely converted from MathJax to Latex.
	   - Citations / references are nicely converted into /texcite and /autocite tags.
	   - All of the basic (not related to Obsidian) tags are converted nicely. 
   - **Applies `obsidian-labels.lua`**, which:
     - *Slugifies* the file name and each heading text  
     - Appends `\label{<file>--<heading>}` to every heading  
   - **Produces** a raw `.tex` in `content/` with all your `\autocite`, `\textcite`, bold/italics, lists and tables intact, but **leaves** any `[[wikilinks]]` or `![[…png]]` embeds untouched (for further postprocessing).

2. **Stage 2** (`postprocess.py`):  
   - **Scans** every `content/*.tex` and:
   - **Rewrites** Obsidian‐style embeds  

```tex
!{[}{[}Image.png{]}{]}
```  
into (full‐width images, two blank lines after):
```tex
\includegraphics[width=\textwidth]{obsidian-md/attachments/Image.png}
```  

- **Converts** any residual  
```tex
{[}{[}Note#Heading|Alias{]}{]}
```  
into slug‐normalizing the label.  
```tex
\hyperref[heading]{Alias}
```  

- **Transforms** Pandoc’s ugly `longtable` output into nice `tabularx` tables:
    - **Portrait** (`≤5` columns) → `table` + `tabularx` at `\textwidth`  
    - **Landscape** (`>5` columns) → `sidewaystable` + `tabularx` at `\textheight`  
        with floating environments, `\small` font, and page breaks (`\clearpage`).


### Windows
Both stages happen within one bat file:
[Convert Markdown to LaTeX](file:///C:/Obsidian%20Vault/Project/convert-md-to-tex.bat)
(replace the link)
### macOS / Linux
1. **Make scripts executable**:
```bash
chmod +x convert-md-to-tex.sh postprocess.py obsidian-labels.lua
```

2. **Stage 1**: Convert Markdown → raw LaTeX
```bash
./convert-md-to-tex.sh
```
or via Shell Command:  
[Convert Markdown to LaTeX](obsidian://shell-commands/?vault=Obsidian%20Vault&execute=XXX)

3. **Stage 2**: Post-process images, links & tables
```bash
./postprocess.py
```
or via Shell Command:  
[Postprocess in Python](obsidian://shell-commands/?vault=Obsidian%20Vault&execute=XXX)


## File paths

- **Input folder**: By default, the scripts look for Markdown files in `obsidian-md/`.  
  Code: `for %%F in (obsidian-md\*.md) do (` (Windows) or `for file in obsidian-md/*.md; do` (macOS/Linux)  
- **Bibliography file**: The scripts reference `literature/references.bib`.  
  Code: `--bibliography="literature\references.bib"` (Windows) or `--bibliography=literature/references.bib` (macOS/Linux)  
- **Lua filter**: The scripts use `obsidian-labels.lua` to handle Obsidian-style internal links and labels.  
  Code: `--lua-filter=obsidian-labels.lua`  
- **Post-processing (Windows only)**: The Windows script runs a Python script `postprocess.py` to fix images, links, and tables after conversion.  
  Code: `call python postprocess.py`  


## Main: `convert-md-to-tex`

1. **Creates the output folder**: A folder named `content/` is created if it does not already exist.  
   Windows: `if not exist content mkdir content`, macOS: `mkdir -p content`  
2. **Loops through Markdown files**: Every `.md` file in the `obsidian-md/` folder is processed.  
   Windows: `for %%F in (obsidian-md\*.md) do (`, macOS: `for file in obsidian-md/*.md; do`  
3. **Cleans up filenames**: Any spaces in filenames are replaced with underscores.  
   Windows: `set "out=!fname: =_!"`, macOS: `slug="${fname// /_}"`  
4. **Runs Pandoc**: Each file is converted from Markdown to LaTeX with the following options:  
   - Input format: `-f markdown+auto_identifiers`  
   - Output format: `-t latex`  
   - Preserve line breaks: `--wrap=preserve`  
   - Apply Lua filter: `--lua-filter=obsidian-labels.lua`  
   - Bibliography: `--bibliography="literature\references.bib"`  
   - Use BibLaTeX: `--biblatex`  
   - Table handling: `--metadata=table-environment:ltablex` and `--metadata=table-width:\textwidth`  (to overwrite default table settings)
   - Output file: `-o "content\!out!.tex"` (Windows) or `-o "content/$slug.tex"` (macOS)  
1. **Runs post-processing** (Windows only): After conversion, the script calls a Python post-processor.  Code: `call python postprocess.py`. On Mac this is done separately.
2. **Saves output**: For each Markdown file, a corresponding `.tex` file is created in the `content/` folder. Example: `obsidian-md/My Note.md → content/My_Note.tex`  


## Lua Filter: `obsidian-labels.lua`

The `obsidian-labels.lua` file is a **Pandoc Lua filter**. Its purpose is to automatically create stable LaTeX `\label{...}` identifiers for each heading in the converted documents. This filter makes sure that every heading in the exported LaTeX documents automatically gets a unique label of the form `filename--heading`. This is critical for consistent cross-referencing when compiling large documents from many Markdown notes.  This ensures you can reliably reference sections across your exported `.tex` files, even when they come from different Obsidian notes.
- In LaTeX, `\label{...}` lets you reference sections with `\ref{...}` or `\autoref{...}`.
- Without unique labels, references across multiple converted files could collide (e.g., many notes may have a "Introduction" heading).
- By combining the **file name** and **heading text**, this filter guarantees uniqueness and preserves Obsidian’s cross-link semantics in LaTeX form.

1. Slugify function
```lua
local function slugify(s)
  return (s
    :gsub("%s+", "-")         -- replace whitespace with hyphens
    :gsub("[^%w%-]", "")      -- remove all non-alphanumeric/non-hyphen chars
    :lower()                  -- lowercase everything
  )
end
```
- Converts a string into a clean "slug" safe for use in labels.
- Example: `"My First Heading!"` → `"my-first-heading"`

2. Meta function
```lua
function Meta(meta)
  if PANDOC_STATE.input_files and #PANDOC_STATE.input_files > 0 then
    local fn = PANDOC_STATE.input_files[1]:match("([^/\\]+)%.md$")
    if fn then file_slug = slugify(fn) end
  end
end
```
- Runs once at the beginning of conversion.
- Extracts the Markdown **filename** (without extension) and slugifies it.
- Stores it in `file_slug`, so every heading later will carry the file context.
- Example: If the file is `My Notes.md`, then `file_slug = "my-notes"`.
 
3. Header function
```lua
function Header(h)
  if file_slug then
    local hslug = slugify(pandoc.utils.stringify(h.content))
    local lbl   = file_slug .. "--" .. hslug
    table.insert(h.content,
      pandoc.RawInline("latex", "\\label{"..lbl.."}")
    )
  end
  return h
end
```
- Runs on every heading in the document.
- Creates a slug from the heading text.
- Combines it with the file slug to form a unique label:  
    `filename--heading`.
- Inserts this label directly into the LaTeX output.
- Example: In file `My Notes.md`, heading `Background` →  
    `\label{my-notes--background}`.


## Postprocessing: `postprocess.py`

`postprocess.py` is made specifically for Obsidian notes and adds additional useful conversions.
- Turning Obsidian-style **image embeds** and **image links** into proper LaTeX figures and cross-references.
- Turning Obsidian **wikilinks** (including `[[Note#Heading|Alias]]`) into LaTeX cross-references that match the labels added by the Lua filter (`obsidian-labels.lua`).
- Normalizing **tables** so they use stretchy `X` columns and converting `longtable` blocks into floating `table` environments with `tabularx`.
- Performing small, pragmatic LaTeX fixes (underscores in URLs, occasional Pandoc quirks, etc.).    
The script rewrites each `content/*.tex` file **in place**.


### Referencing Headers in Obsidian

After running the Lua filter (`obsidian-labels.lua`), each heading received an attached label, for example in a file `My Notes.md`, heading `Background` ⇒ `\label{my-notes--background}`. `postprocess.py` relies on the convention to convert Obsidian wikilinks like `[[My Notes#Background]]` into LaTeX references that target `my-notes--background`.


### Image Embed
When the Markdown contains an **embed** (`![[...]]`), the script outputs a LaTeX `figure` with `\includegraphics`, an optional caption, and a **figure label**:

**Markdown**
```
![[plots/error_curve.png]]
Pic X: Validation error over epochs
```

**Input (Pandoc LaTeX)**
```tex
!{[}{[}error_curve.png{]}{]}
Pic X: Validation error over epochs
```

**Output (LaTeX)**
```latex
\begin{figure}[h]
  \centering
  \includegraphics[width=\textwidth]{plots/error_curve.png}
  \caption{Pic 3: Validation error over epochs}
  \label{fig:error-curve}
\end{figure}
```

- The figure **label** is derived from the image filename (stem), slugified:
    - `plots/error_curve.png` → `error-curve` ⇒ `\label{fig:error-curve}`
- The figure caption is taken directly from the text below the figure. Remember to put two new lines afterwards!
- Width defaults to `\textwidth` inside figures (good default for page-wide plots).
- The float `[h]` requests placement “here” but still gives LaTeX freedom to move it slightly.


### Image Link → inline reference to the figure

A **link** (`[[...]]` without `!`) to an image **does not** re-embed the image. Instead, it becomes a textual cross-reference to the figure label that would be produced by the embed (or that you included elsewhere):

**Input (Markdown)**
```
As shown in [[plots/error_curve.png]], the loss stabilizes after 20 epochs.
```

**Output (LaTeX)**
```latex
As shown in Figure~\ref{fig:error-curve}, the loss stabilizes after 20 epochs.
```

- The target label is `\ref{fig:<image-stem-slug>}`.
- If you never embedded that image, the reference will be unresolved; either embed it somewhere, or define a corresponding figure and label manually.


### Wikilinks (notes, headings, and aliases)

#### Pattern 1: `[[Note#Heading]]`
Converted to a LaTeX **hyperref** that points to the label created by the Lua filter:

**Markdown**
```
See [[Optimization#Learning Rate Schedule]] for details.
```

**Input (Pandoc LaTeX)**
```tex
See {[}{[}Optimization#Learning Rate Schedule{]}{]} for details.
``` 

**Output (LaTeX)**
```latex
See \hyperref[optimization--learning-rate-schedule]{Learning Rate Schedule} for details.
```

- The reference key is `optimization--learning-rate-schedule` (file slug `optimization`, heading slug `learning-rate-schedule`), matching `\label{optimization--learning-rate-schedule}` that the Lua filter placed under that heading.
- The **link text** uses the heading itself if no alias is provided.

#### Pattern 2: `[[Note#Heading|Alias Text]]`
Same as above, but the **display text** comes from the alias:

**Markdown**
```
Refer to [[Optimization#Learning Rate Schedule|LR schedule]] for details.
```

**Input (Pandoc LaTeX)**
```tex
Refer to {[}{[}Optimization#Learning Rate Schedule|LR schedule{]}{]} for details.
``` 


**Output (LaTeX)**
```latex
Refer to \hyperref[optimization--learning-rate-schedule]{LR schedule} for details.
```

#### Pattern 3: `[[Note]]`
If linking to a note **without** a heading, one of these is typically done:
- Target the note’s **top-level heading** label (if you create one), or
- Decide on a project convention (e.g., map `[[Note]]` to `\hyperref[note--introduction]{Note}`) and enforce it in the script.


### Tables: from `longtable` to floating `table` + `tabularx`
Pandoc frequently emits `longtable` for Markdown tables. The current `postprocess.py` converts each `longtable` **with a caption** to a floating `table` and rebuilds its content as a `tabularx` table that fits horizontally:

**Before (LaTeX from Pandoc)**
```latex
\begin{longtable}{p{3cm}p{5cm}l}
\caption{Results}\label{tbl:results}\\
\toprule
\textbf{Metric} & \textbf{Value} & \textbf{Notes} \\
\midrule
\endfirsthead
\multicolumn{3}{c}%
{\tablename\ \thetable\ -- \textit{Continued from previous page}}\\
\toprule
\textbf{Metric} & \textbf{Value} & \textbf{Notes} \\
\midrule
\endhead
Accuracy & 0.95 & Stable \\
\bottomrule
\end{longtable}
```

**After (LaTeX)**
```latex
\begin{table}[htbp]
  \centering
  \caption{Results}
  \label{tbl:results}
  \begin{tabularx}{\linewidth}{@{}X X l@{}}
    \toprule
    \textbf{Metric} & \textbf{Value} & \textbf{Notes} \\
    \midrule
    Accuracy & 0.95 & Stable \\
    \bottomrule
  \end{tabularx}
\end{table}
```

**What happened**
- The **float** becomes `table[htbp]`, which gives the engine flexibility to place the table well.
- The inner table uses `tabularx` with width `\linewidth` (safest inside different contexts).
- Column specs are normalized to use **stretchy `X` columns** where paragraph widths were fixed (see next section).
- Replaces **fixed-width** paragraph columns (e.g., `p{3cm}`) with `X` columns are **stretchy** when used with `tabularx`/`ltablex` and automatically expand/shrink to fill the target width (`\linewidth` or `\textwidth`)


### Other fixes
- **Underscores in URLs**: The script escapes `_` in the URL part of `\href{...}{...}` so LaTeX doesn’t interpret them as subscript markers.
- **Image filenames with spaces**: If such cases leak through, they’re normalized to avoid LaTeX path issues (spaces are unsafe).
- **Minor repairs**: Occasional brace or option ordering fixes for `\includegraphics` and `\ref`.


### Adjustables
1. **Figure width**
    - Current: `\includegraphics[width=\textwidth]{...}`
    - Alternatives: `\linewidth`, a specific fraction (`0.8\textwidth`), or add `height`/`keepaspectratio`.
2. **Figure placement**
    - Current: `[h]`
    - Alternatives: `[H]` (hard placement, with `\usepackage{float}`), or `[htbp]` for more flexible placement.
3. **Table float & width**
    - Current: floating `table[htbp]` + `tabularx` at `\linewidth`.
    - Alternatives: force `[H]`; switch width to `\textwidth` to match top-level layout.
4. **Multipage tables**
    - Current: converted to floating tables (not multipage).
    - Alternative: rebuild as `ltablex` to keep multipage capability (old `bkp2` approach).
5. **Column spec policy**
    - Current: replace all `p{…}` with `X`.
    - Alternative: partial replacement (e.g., only `p{>something}`), or a whitelist/marker to preserve some `p{…}` columns.
6. **Label formats**
    - Figures: `\label{fig:<image-stem-slug>}`
    - Headings: `\label{<file-slug>--<heading-slug>}` via Lua filter
    - You can rename prefixes (`fig:`→`figure:`) or change the slug policy if you keep it consistent everywhere.
7. **Section page breaks**
    - Current: no automatic `\newpage` before `\section`.
    - Optional: insert page breaks before major sections if desired.
8. **Wikilink behaviors**
    - Current: `[[Note#Heading|Alias]]` → `\hyperref[file--heading]{Alias}`.
    - Optional: use `\autoref{...}` for automatic “Section/Table/Figure” naming; consider `\nameref{...}` to print the heading name.

# Troubleshooting

What to do when citations don't work:
- put a semicolon at the end of a citation
- turn off and on the import and restart obsidian
- don't use the citations plugin, we are doing everything with pandoc and pandoc reference list, integrated directly with zotero

Pandoc's understanding of lists:
- Pandoc will only understand a list if it starts and ends with an enter.

Windows:
If anything goes wrong, the file `convert-md-to-tex-no-postprocess.bat` calls Pandoc with Lua filter but doesn't execute the Python script.