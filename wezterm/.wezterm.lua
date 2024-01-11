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
config.color_scheme = 'Monokai Remastered'
config.font = wezterm.font('Hack Nerd Font', { weight = 'Bold' })
config.font_size = 20.0

config.colors = {
  cursor_bg = '#ffffff',
}

config.show_tabs_in_tab_bar = false
config.hide_tab_bar_if_only_one_tab = true

config.default_prog = { '/opt/homebrew/bin/tmux', '-T 256' }

-- and finally, return the configuration to wezterm
return config
