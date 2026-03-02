## dotfiles setup

This project contains setup files for macOS, Linux (including GitHub Codespaces), and Windows. The configurations are designed to be portable across different platforms.

### Quick Start

#### macOS / Linux

Clone this repository into your home folder, then run the setup script:

```bash
cd ~
git clone https://github.com/yourusername/.dotfiles.git
cd .dotfiles
./setup.sh
```

The script uses [GNU Stow](https://www.gnu.org/software/stow/manual/stow.html) to symlink all configuration folders.

#### Windows

Clone this repository and run the PowerShell setup script (as Administrator for best results):

```powershell
cd $env:USERPROFILE
git clone https://github.com/yourusername/.dotfiles.git
cd .dotfiles
.\setup-windows.ps1
```

The Windows script uses [winget](https://github.com/microsoft/winget-cli) for package installation and creates symlinks for compatible configurations.

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

#### Windows Compatibility

The following tools and configurations work on Windows:

| Tool | Windows Support | Config Location |
|------|-----------------|-----------------|
| Git | Native | `%USERPROFILE%\.gitconfig` |
| Neovim | Native | `%LOCALAPPDATA%\nvim` |
| WezTerm | Native | `%USERPROFILE%\.wezterm.lua` |
| Zed | Native | `%APPDATA%\Zed` |
| fzf | Native | (no config needed) |
| ripgrep | Native | (no config needed) |
| zoxide | Native | (PowerShell profile) |
| lazygit | Native | (no config needed) |
| Node.js | Native | (no config needed) |
| Python | Native | (no config needed) |
| Bun | Native | (no config needed) |

**Not available on Windows:** zsh, oh-my-zsh, tmux, stow, AeroSpace, Rectangle, Alt-Tab

The Windows setup script (`setup-windows.ps1`) will:
1. Install compatible tools via winget
2. Create symlinks for git, neovim, wezterm, and zed configs
3. Set up a PowerShell profile with zoxide and fzf integrations

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

### Testing

This repository includes automated testing to validate configurations before deployment.

#### Run Tests Locally

```bash
./test.sh
```

The test script validates:
- Shell script syntax (setup.sh) using shellcheck
- Zsh configuration syntax
- Lua configurations (Neovim, WezTerm)
- TOML configurations (AeroSpace)
- Git configuration
- Tmux configuration

Install validation tools for complete testing:

```bash
# macOS
brew install shellcheck lua taplo

# Ubuntu/Debian
sudo apt-get install shellcheck lua5.4
curl -fsSL https://github.com/tamasfe/taplo/releases/latest/download/taplo-linux-x86_64.gz | gunzip -c > /usr/local/bin/taplo
sudo chmod +x /usr/local/bin/taplo
```

#### Continuous Integration

GitHub Actions automatically tests the dotfiles on every push:
- **Syntax Validation**: Checks all config files for syntax errors
- **macOS Installation**: Tests complete setup on macOS
- **Linux Installation**: Tests complete setup on Ubuntu
- **Stow Symlinks**: Validates symlink creation without conflicts

View test results in the [Actions tab](../../actions) of the repository.
