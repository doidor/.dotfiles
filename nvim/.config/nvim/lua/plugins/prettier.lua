return {
  "prettier/vim-prettier",

  event = { 'BufReadPre', 'BufNewFile' },

  config = function ()
    vim.keymap.set("n", "<leader>p", vim.cmd.Prettier)
  end
}
