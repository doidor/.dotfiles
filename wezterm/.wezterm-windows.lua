-- WezTerm configuration for Windows
-- This config is adapted for Windows and doesn't require tmux

local wezterm = require 'wezterm'

local config = {}

if wezterm.config_builder then
  config = wezterm.config_builder()
end

-- Color scheme
config.color_scheme = 'Monokai Soda'

-- Font configuration
config.font = wezterm.font('ProFont IIx Nerd Font Mono', { weight = 'Bold' })
config.font_size = 14.0  -- Slightly smaller for Windows displays

-- Fallback fonts if ProFont is not installed
config.font = wezterm.font_with_fallback {
  { family = 'ProFont IIx Nerd Font Mono', weight = 'Bold' },
  { family = 'Hack Nerd Font', weight = 'Bold' },
  { family = 'JetBrains Mono', weight = 'Bold' },
  { family = 'Cascadia Code', weight = 'Bold' },
  { family = 'Consolas' },
}

-- Cursor
config.colors = {
  cursor_bg = '#ffffff',
}

-- Tab bar
config.show_tabs_in_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true
config.use_fancy_tab_bar = false

-- Use PowerShell as default shell on Windows
config.default_prog = { 'pwsh.exe', '-NoLogo' }

-- Fallback to Windows PowerShell if pwsh is not installed
if not wezterm.target_triple:find('windows') then
  -- Not on Windows, use default shell
  config.default_prog = nil
else
  -- Check if PowerShell 7+ is available, otherwise fall back to Windows PowerShell
  local success, _ = pcall(function()
    wezterm.run_child_process({ 'pwsh.exe', '-Version' })
  end)
  if not success then
    config.default_prog = { 'powershell.exe', '-NoLogo' }
  end
end

-- Window configuration
config.window_padding = {
  left = 5,
  right = 5,
  top = 5,
  bottom = 5,
}

-- Key bindings (similar to tmux-style navigation)
config.keys = {
  -- Pane splitting (like tmux)
  { key = '|', mods = 'CTRL|SHIFT', action = wezterm.action.SplitHorizontal { domain = 'CurrentPaneDomain' } },
  { key = '_', mods = 'CTRL|SHIFT', action = wezterm.action.SplitVertical { domain = 'CurrentPaneDomain' } },
  
  -- Pane navigation
  { key = 'h', mods = 'CTRL|SHIFT', action = wezterm.action.ActivatePaneDirection 'Left' },
  { key = 'l', mods = 'CTRL|SHIFT', action = wezterm.action.ActivatePaneDirection 'Right' },
  { key = 'k', mods = 'CTRL|SHIFT', action = wezterm.action.ActivatePaneDirection 'Up' },
  { key = 'j', mods = 'CTRL|SHIFT', action = wezterm.action.ActivatePaneDirection 'Down' },
  
  -- Tab navigation
  { key = 't', mods = 'CTRL|SHIFT', action = wezterm.action.SpawnTab 'CurrentPaneDomain' },
  { key = 'w', mods = 'CTRL|SHIFT', action = wezterm.action.CloseCurrentTab { confirm = true } },
  { key = '[', mods = 'CTRL|SHIFT', action = wezterm.action.ActivateTabRelative(-1) },
  { key = ']', mods = 'CTRL|SHIFT', action = wezterm.action.ActivateTabRelative(1) },
  
  -- Copy/Paste
  { key = 'c', mods = 'CTRL|SHIFT', action = wezterm.action.CopyTo 'Clipboard' },
  { key = 'v', mods = 'CTRL|SHIFT', action = wezterm.action.PasteFrom 'Clipboard' },
}

return config
