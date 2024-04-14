return {
  'stevearc/oil.nvim',

  opts = {},

  -- Optional dependencies
  dependencies = { "nvim-tree/nvim-web-devicons" },

  config = function ()
    require("oil").setup({
      view_options = {
        show_hidden = true
      },
      keymaps = {
        ['<C-p>'] = false,
      }
    })

    vim.keymap.set("n", "-", "<CMD>Oil<CR>", { desc = "Open parent directory" })
  end
}
