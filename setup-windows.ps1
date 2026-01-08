#Requires -Version 5.1
<#
.SYNOPSIS
    Windows dotfiles setup script
.DESCRIPTION
    Installs Windows-compatible tools and symlinks configurations.
    Run this script in PowerShell as Administrator for best results.
.NOTES
    Some tools require Administrator privileges to install or create symlinks.
#>

param(
    [switch]$SkipInstall,
    [switch]$SkipSymlinks
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Header { param($Message) Write-Host "`n==> $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[!] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[X] $Message" -ForegroundColor Red }

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check if a command exists
function Test-Command {
    param($Command)
    return [bool](Get-Command -Name $Command -ErrorAction SilentlyContinue)
}

# Install winget if not present (Windows 10 1709+ / Windows 11)
function Install-Winget {
    if (Test-Command "winget") {
        Write-Success "winget already installed"
        return
    }
    
    Write-Header "Installing winget..."
    
    # Try to install via Microsoft Store
    try {
        Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe
        Write-Success "winget installed"
    }
    catch {
        Write-Error "Could not install winget automatically."
        Write-Host "Please install 'App Installer' from the Microsoft Store manually."
        Write-Host "https://apps.microsoft.com/store/detail/9NBLGGH4NNS1"
        exit 1
    }
}

# Install a package via winget
function Install-WingetPackage {
    param(
        [string]$PackageId,
        [string]$Name
    )
    
    $installed = winget list --id $PackageId 2>$null | Select-String $PackageId
    if ($installed) {
        Write-Success "$Name already installed"
    }
    else {
        Write-Host "  Installing $Name..."
        winget install --id $PackageId --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$Name installed"
        }
        else {
            Write-Warning "Failed to install $Name"
        }
    }
}

# Create a symbolic link (requires Administrator or Developer Mode)
function New-SymlinkSafe {
    param(
        [string]$Link,
        [string]$Target,
        [switch]$IsDirectory
    )
    
    # Remove existing link or file
    if (Test-Path $Link) {
        $item = Get-Item $Link -Force
        if ($item.LinkType -eq "SymbolicLink") {
            Remove-Item $Link -Force
        }
        else {
            $backupPath = "$Link.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Move-Item $Link $backupPath -Force
            Write-Warning "Backed up existing $Link to $backupPath"
        }
    }
    
    # Ensure parent directory exists
    $parentDir = Split-Path $Link -Parent
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }
    
    try {
        if ($IsDirectory) {
            New-Item -ItemType SymbolicLink -Path $Link -Target $Target -Force | Out-Null
        }
        else {
            New-Item -ItemType SymbolicLink -Path $Link -Target $Target -Force | Out-Null
        }
        Write-Success "Linked $Link -> $Target"
    }
    catch {
        Write-Warning "Could not create symlink for $Link (try running as Administrator)"
        Write-Host "  Copying instead..."
        if ($IsDirectory) {
            Copy-Item -Path $Target -Destination $Link -Recurse -Force
        }
        else {
            Copy-Item -Path $Target -Destination $Link -Force
        }
        Write-Success "Copied $Target to $Link"
    }
}

# Main installation
function Install-Tools {
    Write-Header "Installing Windows-compatible tools..."
    
    Install-Winget
    
    # Core tools
    Write-Header "Installing core development tools..."
    Install-WingetPackage "Git.Git" "Git"
    Install-WingetPackage "Neovim.Neovim" "Neovim"
    Install-WingetPackage "wez.wezterm" "WezTerm"
    Install-WingetPackage "junegunn.fzf" "fzf"
    Install-WingetPackage "BurntSushi.ripgrep.MSVC" "ripgrep"
    
    # Shell enhancements
    Write-Header "Installing shell enhancements..."
    Install-WingetPackage "ajeetdsouza.zoxide" "zoxide"
    Install-WingetPackage "JesseDuffield.lazygit" "lazygit"
    
    # Runtime & version managers
    Write-Header "Installing runtimes..."
    Install-WingetPackage "OpenJS.NodeJS.LTS" "Node.js LTS"
    Install-WingetPackage "Python.Python.3.12" "Python 3.12"
    Install-WingetPackage "Oven-sh.Bun" "Bun"
    
    # Optional: Editors
    Write-Header "Installing editors..."
    Install-WingetPackage "Zed.Zed" "Zed"
    
    Write-Success "Tool installation complete"
}

# Setup symlinks for configurations
function Install-Symlinks {
    Write-Header "Setting up configuration symlinks..."
    
    $dotfilesDir = $PSScriptRoot
    $homeDir = $env:USERPROFILE
    $appDataLocal = $env:LOCALAPPDATA
    $appDataRoaming = $env:APPDATA
    
    # Git config -> %USERPROFILE%\.gitconfig
    $gitSource = Join-Path $dotfilesDir "git\.gitconfig"
    $gitTarget = Join-Path $homeDir ".gitconfig"
    if (Test-Path $gitSource) {
        New-SymlinkSafe -Link $gitTarget -Target $gitSource
    }
    
    # Neovim config -> %LOCALAPPDATA%\nvim
    $nvimSource = Join-Path $dotfilesDir "nvim\.config\nvim"
    $nvimTarget = Join-Path $appDataLocal "nvim"
    if (Test-Path $nvimSource) {
        New-SymlinkSafe -Link $nvimTarget -Target $nvimSource -IsDirectory
    }
    
    # WezTerm config -> %USERPROFILE%\.wezterm.lua
    # Use Windows-specific config if available, otherwise adapt the standard one
    $weztermSourceWin = Join-Path $dotfilesDir "wezterm\.wezterm-windows.lua"
    $weztermSource = Join-Path $dotfilesDir "wezterm\.wezterm.lua"
    $weztermTarget = Join-Path $homeDir ".wezterm.lua"
    if (Test-Path $weztermSourceWin) {
        New-SymlinkSafe -Link $weztermTarget -Target $weztermSourceWin
    }
    elseif (Test-Path $weztermSource) {
        New-SymlinkSafe -Link $weztermTarget -Target $weztermSource
    }
    
    # Zed config -> %APPDATA%\Zed\settings.json and keymap.json
    $zedSource = Join-Path $dotfilesDir "zed\.config\zed"
    $zedTarget = Join-Path $appDataRoaming "Zed"
    if (Test-Path $zedSource) {
        # Ensure Zed directory exists
        if (-not (Test-Path $zedTarget)) {
            New-Item -ItemType Directory -Path $zedTarget -Force | Out-Null
        }
        
        $zedSettingsSource = Join-Path $zedSource "settings.json"
        $zedSettingsTarget = Join-Path $zedTarget "settings.json"
        if (Test-Path $zedSettingsSource) {
            New-SymlinkSafe -Link $zedSettingsTarget -Target $zedSettingsSource
        }
        
        $zedKeymapSource = Join-Path $zedSource "keymap.json"
        $zedKeymapTarget = Join-Path $zedTarget "keymap.json"
        if (Test-Path $zedKeymapSource) {
            New-SymlinkSafe -Link $zedKeymapTarget -Target $zedKeymapSource
        }
    }
    
    Write-Success "Symlinks configured"
}

# Setup PowerShell profile with useful integrations
function Install-PowerShellProfile {
    Write-Header "Setting up PowerShell profile..."
    
    $profileDir = Split-Path $PROFILE -Parent
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    
    # Check if profile already has our additions
    $profileContent = ""
    if (Test-Path $PROFILE) {
        $profileContent = Get-Content $PROFILE -Raw
    }
    
    $additions = @"

# === Dotfiles additions ===

# Zoxide (smart cd)
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression (& { (zoxide init powershell | Out-String) })
}

# fzf key bindings
if (Get-Command fzf -ErrorAction SilentlyContinue) {
    Set-PSReadLineKeyHandler -Key Ctrl+r -ScriptBlock {
        `$line = `$null
        `$cursor = `$null
        [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]`$line, [ref]`$cursor)
        `$history = Get-Content (Get-PSReadLineOption).HistorySavePath | Select-Object -Unique
        `$result = `$history | fzf --tac --no-sort
        if (`$result) {
            [Microsoft.PowerShell.PSConsoleReadLine]::RevertLine()
            [Microsoft.PowerShell.PSConsoleReadLine]::Insert(`$result)
        }
    }
}

# Aliases
Set-Alias -Name e -Value nvim
Set-Alias -Name lg -Value lazygit

# Editor
`$env:EDITOR = "nvim"

# === End dotfiles additions ===
"@
    
    if ($profileContent -notlike "*Dotfiles additions*") {
        Add-Content -Path $PROFILE -Value $additions
        Write-Success "PowerShell profile updated: $PROFILE"
    }
    else {
        Write-Success "PowerShell profile already configured"
    }
}

# Main
function Main {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host "    Windows Dotfiles Setup Script" -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host ""
    
    if (-not (Test-Administrator)) {
        Write-Warning "Not running as Administrator. Some features may not work."
        Write-Host "  For best results, run PowerShell as Administrator."
        Write-Host ""
    }
    
    if (-not $SkipInstall) {
        Install-Tools
    }
    
    if (-not $SkipSymlinks) {
        Install-Symlinks
        Install-PowerShellProfile
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "      Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Restart your terminal"
    Write-Host "  2. Run 'nvim' to install Neovim plugins"
    Write-Host "  3. Open WezTerm as your terminal"
    Write-Host ""
    Write-Host "Optional manual installations:"
    Write-Host "  - nvm-windows: https://github.com/coreybutler/nvm-windows"
    Write-Host "  - pyenv-win: https://github.com/pyenv-win/pyenv-win"
    Write-Host "  - LM Studio: https://lmstudio.ai/"
    Write-Host ""
}

Main
