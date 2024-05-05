return {
  "ernstwi/juggler.nvim",
  opts = {},
  keys = {
    {
      "<leader>j",
      function()
        require("juggler").activate()
      end,
      desc = "Juggler",
    },
  },
  dependencies = {
    "nvimtools/hydra.nvim",
  },
}
