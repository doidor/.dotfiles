vim.g.mapleader = " "

vim.keymap.set("v", "J", ":m '>+1<CR>gv=gv")
vim.keymap.set("v", "K", ":m '<-2<CR>gv=gv")

vim.keymap.set("n", "J", "mzJ`z")
vim.keymap.set("n", "<C-d>", "<C-d>zz")
vim.keymap.set("n", "<C-u>", "<C-u>zz")
vim.keymap.set("n", "n", "nzzzv")
vim.keymap.set("n", "N", "Nzzzv")

vim.keymap.set("n", "<leader>vwm", function()
  require("vim-with-me").StartVimWithMe()
end)
vim.keymap.set("n", "<leader>svwm", function()
  require("vim-with-me").StopVimWithMe()
end)

-- greatest remap ever
vim.keymap.set("x", "<leader>p", [["_dP]])

-- next greatest remap ever : asbjornHaland
vim.keymap.set({ "n", "v" }, "<leader>y", [["+y]])
vim.keymap.set("n", "<leader>Y", [["+Y]])

vim.keymap.set({ "n", "v" }, "<leader>d", [["_d]])

-- This is going to get me cancelled
vim.keymap.set("i", "<C-c>", "<Esc>")

vim.keymap.set("n", "Q", "<nop>")
vim.keymap.set("n", "<leader>f", vim.lsp.buf.format)

vim.keymap.set("n", "<C-k>", "<cmd>cnext<CR>zz")
vim.keymap.set("n", "<C-j>", "<cmd>cprev<CR>zz")
vim.keymap.set("n", "<leader>k", "<cmd>lnext<CR>zz")
vim.keymap.set("n", "<leader>j", "<cmd>lprev<CR>zz")

vim.keymap.set("n", "<leader>s", [[:%s/\<<C-r><C-w>\>/<C-r><C-w>/gI<Left><Left><Left>]])
vim.keymap.set("n", "<leader>x", "<cmd>!chmod +x %<CR>", { silent = true })

vim.keymap.set("n", "<leader>vpp", "<cmd>e ~/src/nvim-config/lua/doidor/packer.lua<CR>");
vim.keymap.set("n", "<leader>mr", "<cmd>CellularAutomaton make_it_rain<CR>");

vim.keymap.set("n", "<leader>p", vim.cmd.Prettier)

vim.keymap.set("n", "-", ":Fern . -reveal=%<CR>")
vim.keymap.set("n", "<leader>-", ":Fern . -reveal=% -drawer -toggle -width=50<CR>")

vim.keymap.set("n", "<leader>1", "<Plug>BufTabLine.Go(1)")
vim.keymap.set("n", "<leader>2", "<Plug>BufTabLine.Go(2)")
vim.keymap.set("n", "<leader>3", "<Plug>BufTabLine.Go(3)")
vim.keymap.set("n", "<leader>4", "<Plug>BufTabLine.Go(4)")
vim.keymap.set("n", "<leader>5", "<Plug>BufTabLine.Go(5)")
vim.keymap.set("n", "<leader>6", "<Plug>BufTabLine.Go(6)")
vim.keymap.set("n", "<leader>7", "<Plug>BufTabLine.Go(7)")
vim.keymap.set("n", "<leader>8", "<Plug>BufTabLine.Go(8)")
vim.keymap.set("n", "<leader>9", "<Plug>BufTabLine.Go(9)")
vim.keymap.set("n", "<leader>10", "<Plug>BufTabLine.Go(10)")

vim.keymap.set("n", "<leader>w", '<cmd>bd<CR>')
vim.keymap.set("n", "<leader>ww", '<cmd>bufdo bd<CR>')
