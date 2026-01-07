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
- The setup script is idempotent - safe to run multiple times

## Making Changes

1. Edit files directly in this repository
2. Run `./test.sh` to validate syntax before committing
3. Run `stow <folder>` to apply changes, or `./setup.sh` for full reinstall

## Dependencies

The setup script automatically installs:
- Homebrew (package manager)
- Core tools: neovim, tmux, fzf, ripgrep, WezTerm
- Shell: zsh, oh-my-zsh, zsh-autosuggestions, zsh-syntax-highlighting
- Enhancements: zoxide, direnv, lazygit
- Version managers: nvm, pyenv, bun
- AI tools: opencode
- macOS apps: AeroSpace, Rectangle, Alt-Tab
