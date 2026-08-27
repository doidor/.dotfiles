vim.keymap.set("v", "J", ":m '>+1<CR>gv=gv")
vim.keymap.set("v", "K", ":m '<-2<CR>gv=gv")

vim.keymap.set("n", "J", "mzJ`z")
vim.keymap.set("n", "<C-d>", "<C-d>zz")
vim.keymap.set("n", "<C-u>", "<C-u>zz")
vim.keymap.set("n", "n", "nzzzv")
vim.keymap.set("n", "N", "Nzzzv")

vim.keymap.set("x", "<leader>p", [["_dP]])

vim.keymap.set({ "n", "v" }, "<leader>y", [["+y]])
vim.keymap.set("n", "<leader>Y", [["+Y]])

vim.keymap.set({ "n", "v" }, "<leader>d", [["_d]])

vim.keymap.set("i", "<C-c>", "<Esc>")

vim.keymap.set("n", "Q", "<nop>")
vim.keymap.set("n", "<leader>f", vim.lsp.buf.format)

vim.keymap.set("n", "<C-k>", "<cmd>cnext<CR>zz")
vim.keymap.set("n", "<C-j>", "<cmd>cprev<CR>zz")
vim.keymap.set("n", "<leader>k", "<cmd>lnext<CR>zz")
vim.keymap.set("n", "<leader>j", "<cmd>lprev<CR>zz")

vim.keymap.set("n", "<leader>s", [[:%s/\<<C-r><C-w>\>/<C-r><C-w>/gI<Left><Left><Left>]])
vim.keymap.set("n", "<leader>x", "<cmd>!chmod +x %<CR>", { silent = true })

-- Oil buffers are named "oil:///real/path", so the directory is unwrapped
-- instead of yanking the URL.
local function buffer_path()
  local name = vim.api.nvim_buf_get_name(0)
  if name == "" then
    return nil
  end

  local oil_dir = name:match("^oil://(.*)$")
  if oil_dir then
    return (oil_dir:gsub("(.)/$", "%1"))
  end

  return vim.fn.fnamemodify(name, ":p")
end

local function copy_path(mods)
  local path = buffer_path()
  if not path then
    vim.notify("Buffer is not backed by a file", vim.log.levels.WARN)
    return
  end

  path = vim.fn.fnamemodify(path, mods)
  vim.fn.setreg("+", path)
  vim.notify(path, vim.log.levels.INFO, { title = "Copied path" })
end

vim.keymap.set("n", "<leader>cp", function() copy_path(":p") end, { desc = "Copy absolute path" })
vim.keymap.set("n", "<leader>cP", function() copy_path(":.") end, { desc = "Copy path relative to cwd" })

if vim.g.neovide then
  vim.keymap.set('n', '<D-s>', ':w<CR>') -- Save
  vim.keymap.set('v', '<D-c>', '"+y') -- Copy
  vim.keymap.set('n', '<D-v>', '"+P') -- Paste normal mode
  vim.keymap.set('v', '<D-v>', '"+P') -- Paste visual mode
  vim.keymap.set('c', '<D-v>', '<C-R>+') -- Paste command mode
  vim.keymap.set('i', '<D-v>', '<ESC>l"+Pli') -- Paste insert mode
end
