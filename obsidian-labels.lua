-- slugify the filename and append \label{file--heading} on headers

local file_slug = nil

local function slugify(s)
  return (s
    :gsub("%s+", "-")
    :gsub("[^%w%-]", "")
    :lower()
  )
end

function Meta(meta)
  if PANDOC_STATE.input_files and #PANDOC_STATE.input_files > 0 then
    local fn = PANDOC_STATE.input_files[1]:match("([^/\\]+)%.md$")
    if fn then file_slug = slugify(fn) end
  end
end

function Header(h)
  if file_slug then
    local hslug = slugify(pandoc.utils.stringify(h.content))
    local lbl   = file_slug .. "--" .. hslug
    -- append the \label{…}
    table.insert(h.content,
      pandoc.RawInline("latex", "\\label{"..lbl.."}")
    )
  end
  return h
end
