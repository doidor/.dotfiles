#!/usr/bin/env bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}==>${NC} ${1}"
}

print_success() {
    echo -e "${GREEN}✓${NC} ${1}"
}

print_warning() {
    echo -e "${YELLOW}!${NC} ${1}"
}

print_error() {
    echo -e "${RED}✗${NC} ${1}"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin)
            OS="macos"
            print_success "Detected macOS"
            ;;
        Linux)
            OS="linux"
            print_success "Detected Linux"
            ;;
        *)
            print_error "Unsupported operating system"
            exit 1
            ;;
    esac
}

# Install Homebrew
install_homebrew() {
    if command_exists brew; then
        print_success "Homebrew already installed"
    else
        print_header "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH for this session
        if [ "$OS" = "macos" ]; then
            if [ -d "/opt/homebrew" ]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            else
                eval "$(/usr/local/bin/brew shellenv)"
            fi
        else
            eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
        fi
        print_success "Homebrew installed"
    fi
}

# Install required tools
install_required_tools() {
    print_header "Installing required tools..."

    # Git (usually pre-installed)
    if command_exists git; then
        print_success "git already installed"
    else
        brew install git
        print_success "git installed"
    fi

    # Stow
    if command_exists stow; then
        print_success "stow already installed"
    else
        brew install stow
        print_success "stow installed"
    fi

    # Zsh (usually pre-installed)
    if command_exists zsh; then
        print_success "zsh already installed"
    else
        brew install zsh
        print_success "zsh installed"
    fi

    # Set zsh as default shell if not already
    if [ "$SHELL" != "$(command -v zsh)" ]; then
        print_header "Setting zsh as default shell..."
        ZSH_PATH=$(command -v zsh)

        # Add zsh to /etc/shells if not present
        if ! grep -q "$ZSH_PATH" /etc/shells 2>/dev/null; then
            echo "$ZSH_PATH" | sudo tee -a /etc/shells >/dev/null
        fi

        # Change default shell
        if command_exists chsh; then
            chsh -s "$ZSH_PATH" || print_warning "Could not change default shell. Try: chsh -s $ZSH_PATH"
            print_success "Default shell set to zsh (will take effect on next login)"
        else
            print_warning "chsh not available. Default shell not changed."
        fi
    else
        print_success "zsh is already the default shell"
    fi

    # Oh-my-zsh
    if [ -d "$HOME/.oh-my-zsh" ]; then
        print_success "oh-my-zsh already installed"
    else
        print_header "Installing oh-my-zsh..."
        sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
        print_success "oh-my-zsh installed"
    fi
}

# Install oh-my-zsh custom plugins
install_omz_plugins() {
    print_header "Installing oh-my-zsh custom plugins..."

    local plugin_dir="$HOME/.oh-my-zsh/custom/plugins"

    # zsh-autosuggestions
    if [ -d "$plugin_dir/zsh-autosuggestions" ]; then
        print_success "zsh-autosuggestions already installed"
    else
        git clone https://github.com/zsh-users/zsh-autosuggestions.git "$plugin_dir/zsh-autosuggestions"
        print_success "zsh-autosuggestions installed"
    fi

    # zsh-syntax-highlighting
    if [ -d "$plugin_dir/zsh-syntax-highlighting" ]; then
        print_success "zsh-syntax-highlighting already installed"
    else
        git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$plugin_dir/zsh-syntax-highlighting"
        print_success "zsh-syntax-highlighting installed"
    fi

    # zsh-dircolors-solarized
    if [ -d "$plugin_dir/zsh-dircolors-solarized" ]; then
        print_success "zsh-dircolors-solarized already installed"
    else
        git clone https://github.com/seebi/dircolors-solarized.git "$plugin_dir/zsh-dircolors-solarized"
        print_success "zsh-dircolors-solarized installed"
    fi
}

# Install core development tools
install_core_tools() {
    print_header "Installing core development tools..."

    local tools=("neovim" "tmux" "fzf" "ripgrep")

    for tool in "${tools[@]}"; do
        if command_exists "$tool"; then
            print_success "$tool already installed"
        else
            brew install "$tool"
            print_success "$tool installed"
        fi
    done

    # WezTerm (GUI app on macOS, different install)
    if [ "$OS" = "macos" ]; then
        if [ -d "/Applications/WezTerm.app" ]; then
            print_success "WezTerm already installed"
        else
            brew install --cask wezterm
            print_success "WezTerm installed"
        fi
    else
        print_warning "WezTerm installation on Linux varies by distro. Please install manually if needed."
    fi
}

# Install optional shell enhancements
install_shell_enhancements() {
    print_header "Installing shell enhancements..."

    local tools=("zoxide" "direnv" "lazygit")

    for tool in "${tools[@]}"; do
        if command_exists "$tool"; then
            print_success "$tool already installed"
        else
            brew install "$tool"
            print_success "$tool installed"
        fi
    done
}

# Install version managers
install_version_managers() {
    print_header "Installing version managers..."

    # NVM
    if [ -d "$HOME/.nvm" ]; then
        print_success "nvm already installed"
    else
        print_header "Installing nvm..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        print_success "nvm installed"
    fi

    # Pyenv
    if command_exists pyenv; then
        print_success "pyenv already installed"
    else
        brew install pyenv
        print_success "pyenv installed"
    fi

    # Bun
    if command_exists bun; then
        print_success "bun already installed"
    else
        curl -fsSL https://bun.sh/install | bash
        print_success "bun installed"
    fi
}

# Install runtime languages (Node.js, Python)
install_languages() {
    print_header "Installing runtime languages..."

    # Install Node.js via nvm (needed for Mason LSPs)
    if command_exists node; then
        print_success "Node.js already installed ($(node --version))"
    else
        if [ -d "$HOME/.nvm" ]; then
            print_header "Installing Node.js via nvm..."
            # Source nvm to use it in this script
            export NVM_DIR="$HOME/.nvm"
            # shellcheck source=/dev/null
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

            nvm install --lts
            nvm use --lts
            print_success "Node.js installed via nvm"
        else
            print_warning "nvm not found, installing Node.js via Homebrew..."
            brew install node
            print_success "Node.js installed via Homebrew"
        fi
    fi

    # Install Python3 (needed for Mason LSPs)
    if command_exists python3; then
        print_success "Python3 already installed ($(python3 --version))"
    else
        print_header "Installing Python3..."
        if command_exists brew; then
            brew install python3
            print_success "Python3 installed via Homebrew"
        elif command_exists apt-get; then
            sudo apt-get install -y python3 python3-pip
            print_success "Python3 installed via apt"
        else
            print_warning "Could not install Python3 automatically"
        fi
    fi
}

# Install AI coding tools
install_ai_tools() {
    print_header "Installing AI coding tools..."

    # OpenCode - AI coding assistant
    if command_exists opencode; then
        print_success "opencode already installed"
    else
        brew install opencode
        print_success "opencode installed"
    fi
}

# Install macOS-specific tools
install_macos_tools() {
    if [ "$OS" != "macos" ]; then
        return
    fi

    print_header "Installing macOS-specific tools..."

    # AeroSpace
    if [ -d "/Applications/AeroSpace.app" ]; then
        print_success "AeroSpace already installed"
    else
        brew install --cask nikitabobko/tap/aerospace
        print_success "AeroSpace installed"
    fi

    # Rectangle
    if [ -d "/Applications/Rectangle.app" ]; then
        print_success "Rectangle already installed"
    else
        brew install --cask rectangle
        print_success "Rectangle installed"
    fi

    # Alt-Tab
    if [ -d "/Applications/AltTab.app" ]; then
        print_success "Alt-Tab already installed"
    else
        brew install --cask alt-tab
        print_success "Alt-Tab installed"
    fi
}

# Install tmux plugin manager
install_tpm() {
    print_header "Installing tmux plugin manager..."

    if [ -d "$HOME/.tmux/plugins/tpm" ]; then
        print_success "tpm already installed"
    else
        git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
        print_success "tpm installed"
    fi
}

# Stow dotfiles
stow_dotfiles() {
    print_header "Stowing dotfiles..."

    cd "$(dirname "$0")"

    # Backup existing dotfiles that might conflict
    backup_dir="$HOME/.dotfiles-backup-$(date +%Y%m%d-%H%M%S)"
    local needs_backup=false

    # Common dotfiles that might exist
    local common_files=(".zshrc" ".gitconfig" ".tmux.conf" ".wezterm.lua")

    for file in "${common_files[@]}"; do
        if [ -e "$HOME/$file" ] && [ ! -L "$HOME/$file" ]; then
            if [ "$needs_backup" = false ]; then
                mkdir -p "$backup_dir"
                print_warning "Backing up existing dotfiles to $backup_dir"
                needs_backup=true
            fi
            mv "$HOME/$file" "$backup_dir/"
            echo "  Backed up $file"
        fi
    done

    for folder in */; do
        folder="${folder%/}"
        echo "  Stowing $folder..."
        stow -D -t ~ "$folder" 2>/dev/null || true
        stow -t ~ "$folder"
    done

    print_success "Dotfiles stowed"

    if [ "$needs_backup" = true ]; then
        print_warning "Your original dotfiles have been backed up to: $backup_dir"
    fi
}

# Main installation flow
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║     Dotfiles Setup & Installation     ║"
    echo "╔════════════════════════════════════════╗"
    echo -e "${NC}"

    detect_os
    install_homebrew
    install_required_tools
    install_omz_plugins
    install_core_tools
    install_shell_enhancements
    install_version_managers
    install_languages
    install_ai_tools
    install_macos_tools
    install_tpm
    stow_dotfiles

    echo -e "\n${GREEN}╔════════════════════════════════════════╗"
    echo "║         Installation Complete!         ║"
    echo "╚════════════════════════════════════════╝${NC}"
    echo
    print_warning "Please restart your terminal or run: source ~/.zshrc"
    echo
    print_header "Optional manual installations:"
    echo "  - Nix: https://nixos.org/download.html"
    echo "  - pkgx: https://pkgx.sh/"
    echo "  - Fig: https://fig.io/"
    echo "  - LM Studio: https://lmstudio.ai/"
    echo "  - MeetingBar: brew install --cask meetingbar"
    echo
}

# Run main function
main

