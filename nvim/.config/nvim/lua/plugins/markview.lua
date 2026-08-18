return {
  "OXY2DEV/markview.nvim",

  -- Markview lazy-loads itself, so deferring it here would only make previews
  -- appear later. It also has to load after the colorscheme (priority 1000) to
  -- pick up the right highlight groups.
  lazy = false,

  config = function()
    local map = function(lhs, rhs, desc)
      vim.keymap.set("n", lhs, "<cmd>Markview " .. rhs .. "<cr>", { desc = desc, silent = true })
    end

    map("<leader>mm", "toggle", "Markview: toggle preview (buffer)")
    map("<leader>mM", "Toggle", "Markview: toggle preview (all buffers)")
    map("<leader>ms", "splitToggle", "Markview: toggle side-by-side preview")
    map("<leader>mh", "HybridToggle", "Markview: toggle hybrid edit mode")
    map("<leader>ml", "linewiseToggle", "Markview: toggle linewise hybrid mode")
  end
}
