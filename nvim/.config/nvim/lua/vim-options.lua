local augroup = vim.api.nvim_create_augroup
local autocmd = vim.api.nvim_create_autocmd

local doidorGroup = augroup('doidor', {})
local yank_group = augroup('HighlightYank', {})

function R(name)
  print("Reloading...")
  require("plenary.reload").reload_module(name)
end

autocmd('TextYankPost', {
  group = yank_group,
  pattern = '*',
  callback = function()
    vim.highlight.on_yank({
      higroup = 'IncSearch',
      timeout = 40,
    })
  end,
})

autocmd({ "BufWritePre" }, {
  group = doidorGroup,
  pattern = "*",
  command = [[%s/\s\+$//e]],
})


vim.g.netrw_browse_split = 0
vim.g.netrw_banner = 0
vim.g.netrw_winsize = 25
vim.g.blamer_enabled = 1
vim.g.netrw_liststyle = 3
vim.g.netrw_altv = 1
vim.g.netrw_winsize = 25
vim.g.buftabline_numbers = 2
vim.g.buftabline_show = 1
vim.g.buftabline_indicators = true

vim.filetype.add({
  extension = {
    mdx = 'markdown.mdx',
    filename = {},
    pattern = {},
  },
})

vim.opt.cursorline = true
vim.opt.nu = true
vim.opt.relativenumber = true

vim.opt.tabstop = 2
vim.opt.softtabstop = 2
vim.opt.shiftwidth = 2
vim.opt.expandtab = true

vim.opt.smartindent = true

vim.opt.wrap = true

vim.opt.swapfile = false
vim.opt.backup = false
vim.opt.undodir = os.getenv("HOME") .. "/.vim/undodir"
vim.opt.undofile = true

vim.opt.hlsearch = false
vim.opt.incsearch = true

vim.opt.termguicolors = true

vim.opt.scrolloff = 8
vim.opt.signcolumn = "yes"
vim.opt.isfname:append("@-@")

vim.opt.updatetime = 50

vim.opt.colorcolumn = "80"

vim.g.mapleader = " "
