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

When nvm is installed, zsh uses the nearest `.nvmrc` on startup and directory
changes, installs missing Node versions, and restores the default when leaving
a project, following [nvm's zsh integration](https://github.com/nvm-sh/nvm#zsh).

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

### Tmux closing shortcuts

With the `Ctrl+b` prefix, lowercase `x` closes the current pane, `&` closes the
current window, and uppercase `X` closes the entire current tmux session, all
without confirmation.
These are kill operations, not detach: contained programs may stop and unsaved
work may be lost.

Confirmation prompts inside ccmux and tmux's session picker are unchanged.

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
| `prefix + S` | Toggle expanded / compact sidebar (compact mode shows workspace numbers) |
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

After editing the profile, use `prefix + r` inside Herdr to reload both the
attached client's UI settings and the server configuration. The CLI command
`herdr server reload-config` reloads only the server; sidebar changes require
the in-app shortcut.
New Copilot tabs require the same `agency` launcher as the tmux binding.

### Herdr Copilot detection

`herdr/.config/herdr/agent-detection/copilot.toml` overrides Herdr's Copilot
screen-detection manifest. It recognizes all four animated "Waiting for
background agents" markers, preventing false completion notifications between
spinner frames while preserving the existing working and approval-prompt rules.

After editing this manifest, run `stow herdr` and
`herdr server reload-agent-manifests`. This reloads detection without restarting
agents; the regular config-reload shortcut does not reload these rules.
Local manifests replace, rather than extend, the downloaded rules. Remove this
override once upstream includes the fix so future Copilot detection updates can
apply normally.

### Copy tmux layouts into Herdr

`~/.config/herdr/scripts/tmux-to-herdr` takes a read-only JSON snapshot and
recreates it in an explicitly selected, already-running local Herdr session.
It maps tmux sessions to workspaces, windows to tabs, and panes to fresh shells,
preserving session/window names, window order, pane working directories, and
split proportions. It does not move or restart the processes running in tmux,
replay commands, copy environment variables, or copy scrollback.

After adding the helper, run `stow herdr` from this repository. It needs
Python 3.9+, tmux for capture, and Herdr 0.9+ for restore; no Python packages
are required.

```bash
# Capture all sessions on the current tmux server. Existing files are never overwritten.
~/.config/herdr/scripts/tmux-to-herdr snapshot ~/tmux-layout.json

# Open a separate destination in another terminal; keep the tmux sessions running.
herdr --session tmux-import

# Validate the snapshot and destination without creating anything.
~/.config/herdr/scripts/tmux-to-herdr restore ~/tmux-layout.json \
  --herdr-session tmux-import --dry-run

# Recreate the layout. Save the returned tmux-to-Herdr ID mapping for reference.
~/.config/herdr/scripts/tmux-to-herdr restore ~/tmux-layout.json \
  --herdr-session tmux-import > ~/tmux-import-map.json
```

Use repeated `snapshot --session NAME` options to capture only selected tmux
sessions, or `--tmux-socket PATH` to select a different tmux server. Restore
requires either `--herdr-session NAME` (`default` is valid) or
`--herdr-socket PATH`; inherited caller session/pane context cannot override
that destination. Existing destination workspaces are left alone. Imports
refuse duplicate workspace names, including on a second run; use
`--prefix tmux-` or a different destination to avoid collisions.

Missing directories, inconsistent snapshots, labels that conflict with Herdr's
global CLI flags, and splits outside its 10%-90% ratio range fail before
anything is created. Multi-way tmux splits
become balanced binary splits; terminal dimensions and different pane borders
can change exact cell sizes. Linked tmux windows become independent copies in
each workspace. Focus, zoom state, and tmux-specific window/pane indices are
not transferred, and creation uses `--no-focus`.

Do not rearrange tmux panes during capture; the helper rejects a snapshot if
the topology changes. If Herdr fails midway through restoration, the helper
reports the created workspace IDs and leaves partial imports in place rather
than closing shells automatically. Snapshot files are created with mode
`0600` because directory paths and session names may be private; keep them and
the returned ID mapping outside the dotfiles repository.

The optional round-trip test runs real tmux and Herdr instances with a temporary
home directory and dedicated sockets, then shuts down only those test instances:

```bash
HERDR_IMPORT_INTEGRATION=1 python3 -B -m unittest discover \
  -s .github/tests -p 'test_herdr*.py'
```

### Testing

This repository includes automated testing to validate configurations before deployment.

#### Run Tests Locally

```bash
./test.sh
```

The test script validates:
- Shell script syntax (setup.sh) using shellcheck
- Zsh configuration syntax and nvm auto-switching behavior
- Lua configurations (Neovim, WezTerm)
- TOML configurations (AeroSpace, Herdr)
- Herdr launcher and tmux importer behavior without starting agents; keybindings and Copilot detection when Herdr is installed
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
