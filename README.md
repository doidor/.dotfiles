## dotfiles setup

This project contains setup files for macOS and Linux (including GitHub Codespaces). The configurations are designed to be portable across different platforms and Homebrew installations.

To setup everything clone this repository into your home folder (`cd ~`), then run `./setup.sh` to [stow](https://www.gnu.org/software/stow/manual/stow.html) all folders.

### Prerequisites

The dotfiles include availability checks, so missing optional tools won't cause errors. Install what you need based on your workflow.

#### Required Tools

- [zsh](https://www.zsh.org/) - Shell (usually pre-installed on macOS/Linux)
- [oh-my-zsh](https://ohmyz.sh/) - Zsh framework for plugins and themes
- [stow](https://www.gnu.org/software/stow/manual/stow.html) - Symlink manager for dotfiles
- [git](https://git-scm.com/) - Version control (usually pre-installed)

#### Core Development Tools

- [neovim](https://neovim.io/) - Text editor (configured as primary `$EDITOR`)
- [tmux](https://github.com/tmux/tmux) - Terminal multiplexer
- [WezTerm](https://wezfurlong.org/wezterm/) - Terminal emulator (configured to launch tmux)
- [fzf](https://github.com/junegunn/fzf) - Fuzzy finder for command history and files
- [ripgrep](https://github.com/BurntSushi/ripgrep) - Fast text search (rg command)

#### Shell Enhancements (Optional)

- [zoxide](https://github.com/ajeetdsouza/zoxide) - Smart directory jumper (z command)
- [direnv](https://direnv.net/) - Automatic environment variable loading per directory
- [lazygit](https://github.com/jesseduffield/lazygit) - Terminal UI for git

#### Version Managers (Optional)

- [nvm](https://github.com/nvm-sh/nvm) - Node.js version manager
- [pyenv](https://github.com/pyenv/pyenv) - Python version manager
- [bun](https://bun.sh/) - JavaScript runtime and package manager

#### Package Managers (Optional)

- [Homebrew](https://brew.sh/) - Package manager (macOS/Linux)
- [nix](https://nixos.org/download.html) - Declarative package manager
- [pkgx](https://pkgx.sh/) - Package manager

#### macOS Specific (Optional)

- [AeroSpace](https://github.com/nikitabobko/AeroSpace) - Tiling window manager
- [Rectangle](https://rectangleapp.com/) - Window management
- [Alt-Tab](https://alt-tab-macos.netlify.app/) - Windows-style alt-tab
- [MeetingBar](https://github.com/leits/MeetingBar) - Calendar in menu bar

#### Other Optional Tools

- [Fig](https://fig.io/) - Terminal autocomplete and workflows
- [LM Studio](https://lmstudio.ai/) - Local LLM inference

### oh-my-zsh Custom Plugins

The `.zshrc` expects these custom plugins in `~/.oh-my-zsh/custom/plugins/`:

```bash
cd ~/.oh-my-zsh/custom/plugins
git clone https://github.com/zsh-users/zsh-autosuggestions.git
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git
git clone https://github.com/seebi/dircolors-solarized.git zsh-dircolors-solarized
```
