return {
  "windwp/nvim-autopairs",

  event = { 'BufReadPre', 'BufNewFile' },

  config = function()
    require("nvim-autopairs").setup()
  end
}
