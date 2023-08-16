require("doidor.packer").setup()
require("doidor.set")
require("doidor.remap")

local augroup = vim.api.nvim_create_augroup
local autocmd = vim.api.nvim_create_autocmd

local doidorGroup = augroup('doidor', {})
local yank_group = augroup('HighlightYank', {})
local netrw_group = augroup('netrw_mapping', {})
local fern_group = augroup('fern', {})

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


autocmd({ "BufWritePre" }, {
  group = doidorGroup,
  pattern = "*",
  command = "Prettier",
})

-- Pattern hack to ignore Fern
autocmd({ "BufEnter" }, {
  group = fern_group,
  pattern = "/*",
  command = "execute 'FernDo -stay FernReveal ' . @%",
})

autocmd('filetype', {
  group = netrw_group,
  pattern = 'netrw',
  callback = function()
    vim.keymap.set('n', 'l', '<CR>', { remap = true, buffer = true })
  end,
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
  }
})
