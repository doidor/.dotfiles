-- Parsers kept installed up front. The `main` branch dropped `ensure_installed`
-- and `auto_install`, so the list is installed explicitly and anything else is
-- installed on demand by the FileType autocommand below.
local ensure_installed = {
  "bash",
  "c",
  "css",
  "diff",
  "go",
  "html",
  "http",
  "javascript",
  "json",
  "lua",
  "luadoc",
  "markdown",
  "markdown_inline",
  "python",
  "query",
  "regex",
  "rust",
  "toml",
  "tsx",
  "typescript",
  "vim",
  "vimdoc",
  "yaml",
}

-- Compound filetypes ("markdown.mdx" from vim-options.lua) have no parser of
-- their own; the base filetype does. The `master` branch did this internally,
-- `main` does not.
local function buf_lang(bufnr)
  local ft = vim.bo[bufnr].filetype
  if ft == "" then
    return nil
  end

  return vim.treesitter.language.get_lang(ft)
      or vim.treesitter.language.get_lang(vim.split(ft, ".", { plain = true })[1])
end

return {
  {
    "nvim-treesitter/nvim-treesitter",

    -- `master` is frozen and explicitly unsupported on Neovim 0.12: it registers
    -- its query directives with `all = false`, an option 0.12 removed, so every
    -- capture arrives as a node *list*. Opening a markdown file then blew up in
    -- `#set-lang-from-info-string!` (used by its code-fence injection query)
    -- with "attempt to call method 'range' (a nil value)".
    branch = "main",

    -- `main` pins parser revisions to the queries it ships, so parsers must be
    -- rebuilt whenever the plugin updates.
    build = ":TSUpdate",

    -- `main` does not support lazy-loading.
    lazy = false,
    priority = 100,

    config = function()
      local nts = require("nvim-treesitter")

      nts.setup()
      nts.install(ensure_installed)

      local group = vim.api.nvim_create_augroup("doidor_treesitter", { clear = true })

      -- Highlighting and indentation are opt-in on `main`; both used to be
      -- module flags in the `master` setup table.
      local function attach(bufnr, lang)
        if not pcall(vim.treesitter.start, bufnr, lang) then
          return false
        end

        -- Falls back to 'autoindent' by returning -1 for languages that ship no
        -- indents.scm, so this is safe to set unconditionally.
        vim.bo[bufnr].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
        return true
      end

      local installing = {}

      vim.api.nvim_create_autocmd("FileType", {
        group = group,
        callback = function(args)
          local bufnr = args.buf
          local lang = buf_lang(bufnr)
          if not lang or attach(bufnr, lang) then
            return
          end

          -- Stands in for `auto_install`: fetch the parser once, then attach to
          -- any buffer still open on that language.
          if installing[lang] or not vim.tbl_contains(nts.get_available(), lang) then
            return
          end

          installing[lang] = true
          nts.install(lang):await(function()
            installing[lang] = nil
            vim.schedule(function()
              for _, buf in ipairs(vim.api.nvim_list_bufs()) do
                if vim.api.nvim_buf_is_loaded(buf) and buf_lang(buf) == lang then
                  attach(buf, lang)
                end
              end
            end)
          end)
        end,
      })
    end,
  },
}
