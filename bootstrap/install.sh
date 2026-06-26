#!/usr/bin/env bash
#
# Dotfiles bootstrap installer
# -----------------------------
# One-line setup for a fresh machine:
#
#   curl -fsSL https://doidor.github.io/.dotfiles/install.sh | bash
#
# What it does:
#   1. Clones (or updates) doidor/.dotfiles into ~/.dotfiles
#      (uses git when available, otherwise falls back to a tarball download)
#   2. Runs ./setup.sh, which installs dependencies and stows the configs
#
# Optional environment overrides:
#   DOTFILES_REPO      git URL to clone     (default: https://github.com/doidor/.dotfiles.git)
#   DOTFILES_DIR       target directory     (default: $HOME/.dotfiles)
#   DOTFILES_BRANCH    branch to check out  (default: main)
#   DOTFILES_NO_SETUP  if set, skip running setup.sh after fetching

set -euo pipefail

REPO="${DOTFILES_REPO:-https://github.com/doidor/.dotfiles.git}"
DIR="${DOTFILES_DIR:-$HOME/.dotfiles}"
BRANCH="${DOTFILES_BRANCH:-main}"
TARBALL_URL="${DOTFILES_TARBALL:-https://github.com/doidor/.dotfiles/archive/refs/heads/${BRANCH}.tar.gz}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header()  { echo -e "\n${BLUE}==>${NC} ${1}"; }
print_success() { echo -e "${GREEN}✓${NC} ${1}"; }
print_warning() { echo -e "${YELLOW}!${NC} ${1}"; }
print_error()   { echo -e "${RED}✗${NC} ${1}"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

detect_os() {
    case "$(uname -s)" in
        Darwin) OS="macOS" ;;
        Linux)  OS="Linux" ;;
        *)      OS="$(uname -s)" ;;
    esac
    print_success "Detected ${OS}"
}

dir_has_contents() {
    [ -d "$1" ] && [ -n "$(ls -A "$1" 2>/dev/null)" ]
}

clone_with_git() {
    print_header "Cloning ${REPO} into ${DIR}..."
    git clone --branch "$BRANCH" "$REPO" "$DIR"
    print_success "Repository cloned"
}

update_existing() {
    print_header "Existing clone found at ${DIR} — updating..."
    git -C "$DIR" remote set-url origin "$REPO" 2>/dev/null || true
    git -C "$DIR" fetch --quiet origin "$BRANCH"
    git -C "$DIR" checkout --quiet "$BRANCH"
    git -C "$DIR" merge --ff-only --quiet "origin/${BRANCH}" \
        || print_warning "Could not fast-forward; leaving local changes untouched"
    print_success "Repository updated"
}

download_tarball() {
    print_header "git not found — downloading tarball from ${TARBALL_URL}..."
    local tmp
    tmp="$(mktemp -d)"
    # shellcheck disable=SC2064
    trap "rm -rf '${tmp}'" RETURN
    curl -fsSL "$TARBALL_URL" -o "${tmp}/dotfiles.tar.gz"
    tar -xzf "${tmp}/dotfiles.tar.gz" -C "$tmp"
    local extracted
    extracted="$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -n1)"
    if [ -z "$extracted" ]; then
        print_error "Failed to extract tarball"
        exit 1
    fi
    mkdir -p "$DIR"
    cp -R "${extracted}/." "${DIR}/"
    print_success "Downloaded dotfiles (without git history)"
    print_warning "No git metadata yet — will convert to a full clone once git is available"
}

fetch_repo() {
    if [ -d "${DIR}/.git" ]; then
        update_existing
        return
    fi
    if dir_has_contents "$DIR"; then
        print_error "${DIR} already exists and is not a git checkout."
        print_error "Remove it or set DOTFILES_DIR to a different path, then retry."
        exit 1
    fi
    if command_exists git; then
        clone_with_git
    else
        download_tarball
    fi
}

run_setup() {
    if [ -n "${DOTFILES_NO_SETUP:-}" ]; then
        print_warning "DOTFILES_NO_SETUP set — skipping setup.sh"
        return
    fi
    if [ ! -f "${DIR}/setup.sh" ]; then
        print_error "setup.sh not found in ${DIR}"
        exit 1
    fi
    chmod +x "${DIR}/setup.sh" 2>/dev/null || true
    print_header "Running setup.sh..."
    ( cd "$DIR" && ./setup.sh )
}

# If we fetched via tarball, turn the directory into a real git clone now that
# setup.sh has (most likely) installed git. Safe no-op when already a clone.
ensure_git_clone() {
    command_exists git || return 0
    [ -d "${DIR}/.git" ] && return 0
    print_header "Converting ${DIR} into a tracked git clone..."
    git -C "$DIR" init -q
    git -C "$DIR" remote add origin "$REPO" 2>/dev/null \
        || git -C "$DIR" remote set-url origin "$REPO"
    if git -C "$DIR" fetch -q --depth=1 origin "$BRANCH"; then
        git -C "$DIR" reset -q --hard "origin/${BRANCH}"
        git -C "$DIR" checkout -q -B "$BRANCH"
        git -C "$DIR" branch -q --set-upstream-to="origin/${BRANCH}" "$BRANCH" 2>/dev/null || true
        print_success "Git history restored"
    else
        print_warning "Could not fetch git history; dotfiles are in place but not tracked"
    fi
}

main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║        Dotfiles Bootstrap Setup        ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"

    detect_os
    fetch_repo
    run_setup
    ensure_git_clone

    echo
    print_success "All done! Restart your terminal or run: source ~/.zshrc"
}

main "$@"
