require("onedark").setup({
    -- Main options --
    style = 'warm', -- Theme style
    transparent = true,  -- Show/hide background
    term_colors = true, -- Terminal color support
    ending_tildes = false, -- Hide end-of-buffer tildes
    cmp_itemkind_reverse = false, -- Reverse item kind highlights in cmp menu

    -- Toggle theme style --
    toggle_style_key = nil, -- Keybind to toggle theme style
    toggle_style_list = {'dark', 'darker', 'cool', 'deep', 'warm', 'warmer', 'light'},

    -- Change code style --
    code_style = {
        comments = 'italic',
        keywords = 'none',
        functions = 'none',
        strings = 'none',
        variables = 'none'
    },

    -- Lualine options --
    lualine = {
        transparent = false,
    },

    -- Custom colors --
    colors = {
        fg = 'green'
    },

    -- Custom Highlights --
    highlights = {
        ["@string"] = { fg = '#a863ad' },
        ["@none"] = { fg = 'green' },
        Folded = { fg = 'black', bg = 'grey' }
    },

    -- Plugins Config --
    diagnostics = {
        darker = true,
        undercurl = true,
        background = true
    },
})

require("onedark").load()
