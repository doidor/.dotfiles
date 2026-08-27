-- Pull in the wezterm API
local wezterm = require 'wezterm'

-- This table will hold the configuration.
local config = {}

-- In newer versions of wezterm, use the config_builder which will
-- help provide clearer error messages
if wezterm.config_builder then
  config = wezterm.config_builder()
end

-- This is where you actually apply your config choices

-- For example, changing the color scheme:
config.color_scheme = 'Monokai Soda'

-- config.font = wezterm.font('Hack Nerd Font', { weight = 'Bold' })
config.font = wezterm.font('ProFont IIx Nerd Font Mono', { weight = 'Bold' })

config.font_size = 20.0

config.colors = {
  cursor_bg = '#ffffff',
}

config.show_tabs_in_tab_bar = false
config.hide_tab_bar_if_only_one_tab = true

-- Find tmux in common locations (portable across macOS Apple Silicon, Intel, Linux)
local tmux_paths = {
  '/opt/homebrew/bin/tmux',    -- macOS Apple Silicon
  '/usr/local/bin/tmux',        -- macOS Intel
  '/home/linuxbrew/.linuxbrew/bin/tmux',  -- Linux Homebrew
  '/usr/bin/tmux',              -- Linux system
  'tmux',                       -- Fallback to PATH
}

local tmux_cmd = 'tmux'
for _, path in ipairs(tmux_paths) do
  local f = io.open(path, 'r')
  if f ~= nil then
    io.close(f)
    tmux_cmd = path
    break
  end
end

config.default_prog = { tmux_cmd, '-T 256' }

-- and finally, return the configuration to wezterm
return config
