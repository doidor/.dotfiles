return {
  'Asheq/close-buffers.vim',

  config = function ()
    vim.keymap.set("n", "<leader>w", ':Bdelete this<CR>')
    vim.keymap.set("n", "<leader>wa", ':Bdelete other<CR>')
  end
}
