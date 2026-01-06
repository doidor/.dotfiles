#!/bin/bash

# Dotfiles Syntax Validation Script
# Tests configuration files for syntax errors before committing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo -e "${BLUE}🧪 Testing dotfiles configuration...${NC}\n"

# Helper function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Test 1: Shell script syntax with shellcheck
echo -e "${BLUE}→ Checking shell scripts...${NC}"
if command_exists shellcheck; then
    if shellcheck setup.sh; then
        echo -e "${GREEN}✓ setup.sh passed shellcheck${NC}"
    else
        echo -e "${RED}✗ setup.sh has shellcheck issues${NC}"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠ shellcheck not installed, skipping shell script checks${NC}"
    ((WARNINGS++))
fi
echo

# Test 2: Zsh configuration syntax
echo -e "${BLUE}→ Checking zsh configuration...${NC}"
if command_exists zsh; then
    if zsh -n zsh/.zshrc 2>&1; then
        echo -e "${GREEN}✓ .zshrc syntax valid${NC}"
    else
        echo -e "${RED}✗ .zshrc has syntax errors${NC}"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠ zsh not installed, skipping zsh checks${NC}"
    ((WARNINGS++))
fi
echo

# Test 3: Lua configuration files (Neovim & WezTerm)
echo -e "${BLUE}→ Checking lua configurations...${NC}"
if command_exists lua; then
    LUA_ERRORS=0

    # Check WezTerm config
    if [ -f "wezterm/.wezterm.lua" ]; then
        if lua -l wezterm/.wezterm.lua 2>/dev/null; then
            echo -e "${GREEN}✓ .wezterm.lua syntax valid${NC}"
        else
            echo -e "${RED}✗ .wezterm.lua has syntax errors${NC}"
            ((LUA_ERRORS++))
        fi
    fi

    # Check Neovim configs
    if [ -d "nvim/.config/nvim" ]; then
        NVIM_FILES=$(find nvim/.config/nvim -name "*.lua" -type f)
        NVIM_COUNT=0
        NVIM_FAILED=0

        for file in $NVIM_FILES; do
            ((NVIM_COUNT++))
            if ! lua -e "dofile('$file')" 2>/dev/null; then
                if [ $NVIM_FAILED -eq 0 ]; then
                    echo -e "${RED}✗ Neovim lua files with issues:${NC}"
                fi
                echo -e "  ${RED}• $file${NC}"
                ((NVIM_FAILED++))
                ((LUA_ERRORS++))
            fi
        done

        if [ $NVIM_FAILED -eq 0 ]; then
            echo -e "${GREEN}✓ All $NVIM_COUNT neovim lua files valid${NC}"
        else
            echo -e "${RED}✗ $NVIM_FAILED/$NVIM_COUNT neovim lua files have issues${NC}"
        fi
    fi

    if [ $LUA_ERRORS -gt 0 ]; then
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠ lua not installed, skipping lua checks${NC}"
    ((WARNINGS++))
fi
echo

# Test 4: TOML configuration (AeroSpace)
echo -e "${BLUE}→ Checking TOML configurations...${NC}"
if command_exists taplo; then
    if [ -f "aerospace/.aerospace.toml" ]; then
        if taplo check aerospace/.aerospace.toml 2>&1; then
            echo -e "${GREEN}✓ .aerospace.toml syntax valid${NC}"
        else
            echo -e "${RED}✗ .aerospace.toml has syntax errors${NC}"
            ((ERRORS++))
        fi
    fi
elif command_exists toml-cli; then
    if [ -f "aerospace/.aerospace.toml" ]; then
        if toml-cli get aerospace/.aerospace.toml "" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ .aerospace.toml syntax valid${NC}"
        else
            echo -e "${RED}✗ .aerospace.toml has syntax errors${NC}"
            ((ERRORS++))
        fi
    fi
else
    echo -e "${YELLOW}⚠ taplo/toml-cli not installed, skipping TOML checks${NC}"
    ((WARNINGS++))
fi
echo

# Test 5: Git configuration
echo -e "${BLUE}→ Checking git configuration...${NC}"
if command_exists git; then
    if git config -f git/.gitconfig --list >/dev/null 2>&1; then
        echo -e "${GREEN}✓ .gitconfig syntax valid${NC}"
    else
        echo -e "${RED}✗ .gitconfig has syntax errors${NC}"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠ git not installed, skipping git config checks${NC}"
    ((WARNINGS++))
fi
echo

# Test 6: Tmux configuration
echo -e "${BLUE}→ Checking tmux configuration...${NC}"
if command_exists tmux; then
    # Tmux config check is tricky, just verify file exists and is readable
    if [ -f "tmux/.tmux.conf" ] && [ -r "tmux/.tmux.conf" ]; then
        # Basic syntax check - try to parse it
        if tmux -f tmux/.tmux.conf list-keys >/dev/null 2>&1; then
            echo -e "${GREEN}✓ .tmux.conf syntax valid${NC}"
        else
            echo -e "${YELLOW}⚠ .tmux.conf may have issues (or TPM plugins not installed)${NC}"
            ((WARNINGS++))
        fi
    fi
else
    echo -e "${YELLOW}⚠ tmux not installed, skipping tmux config checks${NC}"
    ((WARNINGS++))
fi
echo

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Tests passed with $WARNINGS warning(s)${NC}"
    echo -e "${YELLOW}  (Some validation tools not installed)${NC}"
    exit 0
else
    echo -e "${RED}✗ Tests failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    exit 1
fi
