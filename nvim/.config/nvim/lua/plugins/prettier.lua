return {
  "prettier/vim-prettier",

  config = function ()
    vim.keymap.set("n", "<leader>p", vim.cmd.Prettier)
  end
}
