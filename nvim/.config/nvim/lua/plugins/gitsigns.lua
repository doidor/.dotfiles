return {
  'lewis6991/gitsigns.nvim',

  event = { 'BufReadPre', 'BufNewFile' },

  config = function()
    require('gitsigns').setup({
      on_attach = function(bufnr)
        local gs = require('gitsigns')

        local function map_hunk(key, direction, description)
          vim.keymap.set('n', key, function()
            if vim.wo.diff then
              vim.cmd.normal({ key, bang = true })
            else
              gs.nav_hunk(direction)
            end
          end, { buffer = bufnr, desc = description })
        end

        map_hunk(']c', 'next', 'Next git hunk')
        map_hunk('[c', 'prev', 'Previous git hunk')
        vim.keymap.set('n', '<leader>hp', gs.preview_hunk, { buffer = bufnr, desc = 'Preview git hunk' })
      end,
    })
  end
}
