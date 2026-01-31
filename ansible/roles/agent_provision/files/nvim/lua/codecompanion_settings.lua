
require("codecompanion").setup({
  strategies = {
    chat = {
      adapter = "copilot",
      slash_commands = {
        ["buffer"] = {
          callback = "strategies.chat.slash_commands.buffer",
          opts = {
            provider = "telescope",
            contains_code = true,
          },
        },
        ["file"] = {
          callback = "strategies.chat.slash_commands.file",
          opts = {
            provider = "telescope",
            contains_code = true,
          },
        },
      },
    },
  },
  display = { 
    diff = {
      provider = "mini_diff",
    },
    action_palette = {
      provider = "telescope",
    },
  },
})

-- Expand 'cc' into 'CodeCompanion' in the command line
vim.cmd([[cab cc CodeCompanion]])
vim.api.nvim_set_keymap("n", "<C-a>", ":CodeCompanionActions<CR>", { noremap = true, silent = true })
vim.api.nvim_set_keymap("v", "<C-a>", ":CodeCompanionActions<CR>", { noremap = true, silent = true })
vim.api.nvim_set_keymap("n", "<Leader>ca", ":CodeCompanionChat Toggle<CR>", { noremap = true, silent = true })
vim.api.nvim_set_keymap("v", "<Leader>ca", ":CodeCompanionChat Toggle<CR>", { noremap = true, silent = true })
vim.api.nvim_set_keymap("v", "ga", ":CodeCompanionChat Add<CR>", { noremap = true, silent = true })

