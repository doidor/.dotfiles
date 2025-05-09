return {
  "webhooked/kanso.nvim",
  lazy = false,
  priority = 1000,
  config = function()
    vim.cmd.colorscheme("kanso")
    vim.api.nvim_set_hl(0, "Normal", { bg = "none" })
    vim.api.nvim_set_hl(0, "NormalFloat", { bg = "none" })
    vim.api.nvim_set_hl(0, "Visual", { bg = "#FF92A5", fg = "#ffffff"} )
  end
}

-- return {
--   "EdenEast/nightfox.nvim",

--   config = function ()
--     vim.cmd.colorscheme("nightfox")

--     vim.api.nvim_set_hl(0, "Normal", { bg = "none" })
--     vim.api.nvim_set_hl(0, "NormalFloat", { bg = "none" })
--     vim.api.nvim_set_hl(0, "Visual", { bg = "#FF92A5", fg = "#ffffff"} )
--   end
-- }
