# AGENTS.md

This repository contains personal dotfiles for macOS and Linux systems. The configurations are managed using GNU Stow for symlink management.

## Project Structure

```
.dotfiles/
├── aerospace/          # AeroSpace tiling window manager config (macOS)
├── git/                # Git configuration
├── nvim/               # Neovim configuration (Lua-based)
├── qmk/                # QMK keyboard firmware mappings
├── tmux/               # Tmux terminal multiplexer config
├── vial/               # Vial keyboard configuration
├── wezterm/            # WezTerm terminal emulator config
├── zed/                # Zed editor configuration
├── zsh/                # Zsh shell configuration
├── setup.sh            # Main installation script
└── test.sh             # Configuration validation script
```

## Key Files

- `setup.sh` - Installs all dependencies via Homebrew and stows dotfiles
- `test.sh` - Validates syntax of all configuration files
- `zsh/.zshrc` - Main shell configuration with oh-my-zsh
- `nvim/.config/nvim/init.lua` - Neovim entry point
- `nvim/.config/nvim/lua/plugins.lua` - Plugin definitions (lazy.nvim)
- `tmux/.tmux.conf` - Tmux configuration with TPM plugins
- `wezterm/.wezterm.lua` - WezTerm terminal configuration
- `git/.gitconfig` - Git aliases and settings

## Conventions

- All configurations are organized by tool in top-level directories
- Each directory is structured for GNU Stow (files mirror home directory structure)
- Neovim plugins are in `nvim/.config/nvim/lua/plugins/` as individual Lua files
- tmux pickers live in `tmux/.config/tmux/scripts/` and share one fzf UX:
  `prefix + w` finds windows, `prefix + O` finds agent sessions
- The tmux status bar is hand-rolled in `.tmux.conf`, with no theme plugin. Keep
  it to BMP characters: Nerd Font icons above U+FFFF render as empty boxes in
  this WezTerm build. Box-drawing characters are safe, WezTerm draws those
  itself. Status bar helpers also go in `tmux/.config/tmux/scripts/`, where
  `./test.sh` shellchecks everything.
- Copilot runs one session per tmux window; `prefix + A` opens a new one
- The setup script is idempotent - safe to run multiple times
- Never commit secrets. Machine-local secrets and overrides go in `~/.zshrc.local`
  (git-ignored, sourced by `.zshrc`) and are referenced via env vars. `./test.sh`
  fails if a known secret pattern appears in the repo.

## Making Changes

1. Edit files directly in this repository
2. Run `./test.sh` to validate syntax before committing
3. Run `stow <folder>` to apply changes, or `./setup.sh` for full reinstall

## Dependencies

The setup script automatically installs:
- Homebrew (package manager)
- Core tools: neovim, tmux, fzf, ripgrep, tree-sitter-cli (builds nvim-treesitter
  parsers), WezTerm
- Shell: zsh, oh-my-zsh, zsh-autosuggestions, zsh-syntax-highlighting
- Enhancements: zoxide, direnv, lazygit, chafa (sixel image viewer for tmux)
- Developer CLIs: azure-cli (`az`), gh
- Version managers: nvm, pyenv, bun
- AI tools: opencode, GitHub Copilot CLI (`copilot-cli` cask on macOS, npm elsewhere),
  ccmux (agent session tracker; `prefix + O` opens its picker)
- Fonts: Hack Nerd Font, ProFont Nerd Font (required by WezTerm and Zed configs)
- macOS apps: AeroSpace, Rectangle, Alt-Tab
- macOS startup apps: 1Password, Cotypist, DisplayLink, Logitech G Hub, OpenIn
  (set as default browser), Wispr Flow, and Amphetamine (via `mas`, App Store only)
