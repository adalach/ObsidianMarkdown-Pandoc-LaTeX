--[[
  Pandoc Lua filter: append \label{file--heading} to each heading.
  Enables cross-references when converting Obsidian wikilinks to LaTeX \hyperref.
]]

local file_slug = nil

local function slugify(s)
  return (s
    :gsub("%s+", "-")
    :gsub("[^%w%-]", "")
    :lower()
  )
end

function Meta(meta)
  if PANDOC_STATE and PANDOC_STATE.input_files and #PANDOC_STATE.input_files > 0 then
    local path = PANDOC_STATE.input_files[1]
    local fn = path:match("([^/\\]+)%.md$")
    if fn then
      file_slug = slugify(fn)
    end
  end
  return meta
end

function Header(h)
  if file_slug then
    local hslug = slugify(pandoc.utils.stringify(h.content))
    local lbl   = file_slug .. "--" .. hslug
    return pandoc.Header(h.level, h.content, pandoc.Attr(lbl, {}, {}))
  end
  return h
end
