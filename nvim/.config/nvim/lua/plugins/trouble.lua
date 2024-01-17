return {
  'folke/trouble.nvim',

  dependencies = {
    'nvim-tree/nvim-web-devicons'
  },

  config = function ()
    vim.keymap.set("n", "<leader>pp", function() require("trouble").toggle("document_diagnostics") end)
    vim.keymap.set("n", "<leader>pg", function() require("trouble").toggle("workspace_diagnostics") end)
    vim.keymap.set("n", "gR", function() require("trouble").toggle("lsp_references") end)
    vim.keymap.set("n", "gT", function() require("trouble").toggle("lsp_type_definitions") end)
  end
}
