## dotfiles setup

This project contains setup files for macOS and Linux (including GitHub Codespaces). The configurations are designed to be portable across different platforms and Homebrew installations.

### Quick install (one-liner)

On a fresh machine, bootstrap everything with a single command:

```bash
curl -fsSL https://doidor.github.io/.dotfiles/install.sh | bash
```

This clones the repo into `~/.dotfiles` (or updates it if it already exists) and runs `setup.sh`, which installs dependencies and [stows](https://www.gnu.org/software/stow/manual/stow.html) all folders. The script lives in [`bootstrap/install.sh`](bootstrap/install.sh) and is published to GitHub Pages automatically by [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml).

> The `doidor.github.io` URL redirects to the canonical `https://tudorpopa.com/.dotfiles/install.sh` — both work. Always review a script before piping it into a shell.

You can override the defaults with environment variables:

```bash
# clone somewhere else, or track a different branch
DOTFILES_DIR=~/dev/dotfiles DOTFILES_BRANCH=main \
  bash -c "$(curl -fsSL https://doidor.github.io/.dotfiles/install.sh)"
```

### Manual install

Prefer to do it yourself? Clone into `~/.dotfiles` and run the setup script:

```bash
git clone https://github.com/doidor/.dotfiles.git ~/.dotfiles
cd ~/.dotfiles
./setup.sh
```

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
- [tree-sitter-cli](https://github.com/tree-sitter/tree-sitter) - Builds the parsers nvim-treesitter installs

#### Shell Enhancements (Optional)

- [zoxide](https://github.com/ajeetdsouza/zoxide) - Smart directory jumper (z command)
- [direnv](https://direnv.net/) - Automatic environment variable loading per directory
- [lazygit](https://github.com/jesseduffield/lazygit) - Terminal UI for git
- [hunk](https://github.com/modem-dev/hunk) - Terminal diff review with comments for coding agents

Open the full ccmux picker with `prefix + Ctrl+O`, select a session, and press
`d` to review its working-tree diff in hunk. You can also run `hunk diff` directly.

Setup also installs ccmux's `relay` skill globally for GitHub Copilot, using the
installed ccmux release. Existing relay skills are left unchanged. Use the
picker's `m` menu and **Hand off** action, or ask Copilot to relay an existing
session's response to another session.

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

- [Herdr](https://herdr.dev/) - Optional terminal multiplexer; install separately
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

### Herdr keybindings

The optional Herdr 0.9+ profile lives in `herdr/.config/herdr/`. It maps the
custom tmux shortcuts and common tmux defaults to Herdr-native actions without
changing the tmux or WezTerm configurations. `./setup.sh` stows this package;
Herdr itself is installed separately.

Use one Herdr workspace per project, like a tmux session. Herdr tabs correspond
to tmux windows, and the tab bar sits at the bottom. Separately named Herdr
sessions isolate the entire runtime; they are not needed for normal project
switching.

Here `prefix` means `Ctrl+b`. Keys after the prefix are case-sensitive.

| Shortcut | Herdr action |
| --- | --- |
| `prefix + h/j/k/l` | Focus a pane |
| `prefix + Ctrl+h/j/k/l` | Resize using Herdr's native increments |
| `prefix + %` / `prefix + "` | Split right / down, following the current directory |
| `prefix + c` / `prefix + ,` | Create / rename a tab |
| `prefix + n/p` / `prefix + 1..9` | Next/previous tab / select a tab |
| `prefix + &` / `prefix + x` | Close a tab / pane |
| `prefix + N` | Create a workspace |
| `prefix + w` or `prefix + s` | Native workspace navigation, not the tmux fzf picker |
| `prefix + Ctrl+O` or `prefix + q` | Herdr's go-to picker, not ccmux |
| `prefix + Ctrl+w` or `prefix + ;` | Global last-pane toggle across tabs and workspaces |
| `prefix + A` | Open a Copilot tab using the existing `agency copilot --yolo` launcher |
| `prefix + S` | Show/hide the Herdr sidebar |
| `prefix + r` / `prefix + R` | Reload configuration / enter resize mode |
| `prefix + o` / `prefix + z` | Cycle panes / toggle zoom |
| `prefix + $` / `prefix + (` / `prefix + )` | Rename / previous / next workspace |
| `prefix + Q` / `prefix + g` | Herdr settings / jump to a notification target |
| `prefix + d` / `prefix + ?` | Detach / show active keybindings |

Herdr's built-in `prefix + [` copy mode remains available. `prefix + O` stays
unbound. Resize steps and key repetition follow Herdr's behavior rather than
tmux's five-cell steps and repeat-key window. Use `prefix + R` for Herdr's
continuous resize mode.

The ccmux review/relay UI, tmux buffer and layout commands, and tmux-resurrect's
`prefix + Ctrl+s` / `prefix + Ctrl+r` are not ported. Herdr persists its own
sessions, and its last-pane toggle is not the old window-only MRU history.
Use Herdr's menus for workspace closing. `hunk diff` can still be run directly,
but ccmux's automatic comment hand-back does not target Herdr panes.

After editing the profile, run `herdr server reload-config` or use `prefix + r`.
New Copilot tabs require the same `agency` launcher as the tmux binding.

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
- TOML configurations (AeroSpace, Herdr)
- Herdr launcher behavior without starting agents; Herdr keybindings when its CLI is installed
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
