return {
  "nvim-neo-tree/neo-tree.nvim",

  lazy = false,

  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-tree/nvim-web-devicons", -- not strictly required, but recommended
    "MunifTanjim/nui.nvim",
  },

  config = function ()
    require('neo-tree').setup({
      close_if_last_window = true,

      window = {
        position = "current",
        mappings = {
          ["<cr>"] = "open",
          ["l"] = "open",
          ["h"] = "close_node",
        },
      },

      filesystem = {
        filtered_items = {
          visible = true,
          hide_dotfiles = false,
          hide_gitignored = true,
        },

        follow_current_file = {
          enabled = true,
          leave_dirs_open = true,
        },

        hijack_netrw_behavior = "open_default"
      },
    })

    vim.keymap.set("n", "-", ":Neotree reveal<CR>")
  end
}
