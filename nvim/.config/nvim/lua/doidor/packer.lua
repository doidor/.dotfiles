local M = {}

function M.setup()
  -- Indicate first time installation
  local packer_bootstrap = false

  -- packer.nvim configuration
  local conf = {
    profile = {
      enable = true,
      threshold = 0, -- the amount in ms that a plugins load time must be over for it to be included in the profile
    },

    display = {
      open_fn = function()
        return require("packer.util").float { border = "rounded" }
      end,
    },
  }

  -- Check if packer.nvim is installed
  -- Run PackerCompile if there are changes in this file
  local function packer_init()
    local fn = vim.fn
    local install_path = fn.stdpath "data" .. "/site/pack/packer/start/packer.nvim"
    if fn.empty(fn.glob(install_path)) > 0 then
      packer_bootstrap = fn.system {
        "git",
        "clone",
        "--depth",
        "1",
        "https://github.com/wbthomason/packer.nvim",
        install_path,
      }
      vim.cmd [[packadd packer.nvim]]
    end
    vim.cmd "autocmd BufWritePost plugins.lua source <afile> | PackerCompile"
  end

  -- Plugins
  local function plugins(use)
    use { "wbthomason/packer.nvim" }

    -- Performance
    use { "lewis6991/impatient.nvim" }

    use {
      'nvim-telescope/telescope.nvim', branch = "0.1.x",
      -- or                            , branch = '0.1.x',
      requires = { { 'nvim-lua/plenary.nvim', 'nvim-telescope/telescope-live-grep-args.nvim' } }
    }

    use { 'nvim-telescope/telescope-fzf-native.nvim', run = 'make', cond = vim.fn.executable 'make' == 1,
      cmd = { "Telescope" } }

    use { 'nvim-treesitter/nvim-treesitter', run = ':TSUpdate' }
    use { 'nvim-treesitter/playground', cmd = { 'TSPlaygroundToggle' } }
    use { 'mbbill/undotree', cmd = { "UndotreeToggle" } }

    use {
      'VonHeikemen/lsp-zero.nvim',
      branch = 'v1.x',
      requires = {
        -- LSP Support
        { 'neovim/nvim-lspconfig' },
        { 'williamboman/mason.nvim' },
        { 'williamboman/mason-lspconfig.nvim' },

        -- Autocompletion
        { 'hrsh7th/nvim-cmp' },
        { 'hrsh7th/cmp-buffer' },
        { 'hrsh7th/cmp-path' },
        { 'saadparwaiz1/cmp_luasnip' },
        { 'hrsh7th/cmp-nvim-lsp' },
        { 'hrsh7th/cmp-nvim-lua' },

        -- Snippets
        { 'L3MON4D3/LuaSnip' },
        { 'rafamadriz/friendly-snippets' },
      }
    }

    use { "github/copilot.vim", event = "BufEnter" }

    use { "tpope/vim-surround", event = "BufEnter" }
    use { "tpope/vim-commentary", event = "BufEnter" }
    -- {se("tpope/vim-vinegar")
    use { 'prettier/vim-prettier', event = "BufEnter" }

    use { "RRethy/vim-illuminate", event = "BufEnter" }

    use {
      'nvim-lualine/lualine.nvim',
      requires = { 'kyazdani42/nvim-web-devicons', opt = true }
    }

    use { 'APZelos/blamer.nvim', event = "BufEnter" }
    use { 'airblade/vim-gitgutter', event = "BufEnter" }

    use("EdenEast/nightfox.nvim")
    use('editorconfig/editorconfig-vim')
    use {
      "windwp/nvim-autopairs",
      event = "BufEnter",
      config = function() require("nvim-autopairs").setup {} end
    }

    use('lambdalisue/nerdfont.vim')
    use { 'lambdalisue/fern.vim',
      requires = {
        'lambdalisue/fern-renderer-nerdfont.vim',
        'lambdalisue/fern-hijack.vim',
      },
      config = function()
        vim.g['fern#renderer'] = 'nerdfont'
        vim.g['fern#default_hidden'] = 1
      end
    }

    use {'nvim-tree/nvim-web-devicons'}

    use {'folke/trouble.nvim',
      requires = {
        'nvim-tree/nvim-web-devicons'
      }
    }

    use { 'brenoprata10/nvim-highlight-colors',
      config = function() require('nvim-highlight-colors').setup {} end }

    use { 'akinsho/git-conflict.nvim', tag = "*", config = function()
      require('git-conflict').setup()
    end }

    -- Bootstrap Neovim
    if packer_bootstrap then
      print "Restart Neovim required after installation!"
      require("packer").sync()
    end
  end

  -- Init and start packer
  packer_init()
  local packer = require "packer"

  -- Performance
  pcall(require, "impatient")
  -- pcall(require, "packer_compiled")

  packer.init(conf)
  packer.startup(plugins)
end

return M
