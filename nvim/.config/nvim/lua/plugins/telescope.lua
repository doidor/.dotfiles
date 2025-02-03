return {}
-- return {
--   {
--     'nvim-telescope/telescope.nvim',

--     tag = "0.1.5",

--     dependencies = {
--       'nvim-lua/plenary.nvim',
--       { 'nvim-telescope/telescope-fzf-native.nvim', build = 'make' },
--       'nvim-telescope/telescope-live-grep-args.nvim',
--     },

--     config = function()
--       require('telescope').setup {
--         extensions = {
--           fzf = {
--             fuzzy = true,                    -- false will only do exact matching
--             override_generic_sorter = true,  -- override the generic sorter
--             override_file_sorter = true,     -- override the file sorter
--             case_mode = "smart_case",        -- or "ignore_case" or "respect_case"
--                                              -- the default case_mode is "smart_case"
--           }
--         }
--       }

--       require('telescope').load_extension('fzf')
--       require('telescope').load_extension('live_grep_args')

--       local builtin = require('telescope.builtin')

--       vim.keymap.set('n', '<C-p>', builtin.git_files, {})
--       vim.keymap.set('n', '<leader>ps', function()
--         builtin.grep_string({ search = vim.fn.input("Grep > ") })
--       end)

--       -- See `:help telescope.builtin`
--       vim.keymap.set('n', '<leader><space>', builtin.buffers, { desc = '[ ] Find existing buffers' })
--       vim.keymap.set('n', '<leader>/', function()
--         -- You can pass additional configuration to telescope to change theme, layout, etc.
--         builtin.current_buffer_fuzzy_find(require('telescope.themes').get_dropdown {
--           winblend = 10,
--           previewer = false,
--         })
--       end, { desc = '[/] Fuzzily search in current buffer]' })

--       vim.keymap.set('n', '<leader>sf', function()
--         builtin.find_files({hidden=true})
--       end, { desc = '[S]earch [F]iles' })
--       vim.keymap.set('n', '<leader>sh', builtin.help_tags, { desc = '[S]earch [H]elp' })
--       vim.keymap.set('n', '<leader>sy', builtin.treesitter, { desc = '[S]earch [Y]mbols' })
--       vim.keymap.set('n', '<leader>sw', builtin.grep_string, { desc = '[S]earch current [W]ord' })
--       vim.keymap.set('n', '<leader>sg', require('telescope').extensions.live_grep_args.live_grep_args,
--         { desc = '[S]earch by [G]rep' })
--       vim.keymap.set('n', '<leader>sd', builtin.diagnostics, { desc = '[S]earch [D]iagnostics' })
--       vim.keymap.set('n', '<leader>yr', builtin.registers, { desc = 'Search Registers' })

--     end,
--   },
-- }
