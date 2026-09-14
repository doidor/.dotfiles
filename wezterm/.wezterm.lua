-- Pull in the wezterm API
local wezterm = require 'wezterm'

-- Temporary trial: set to false to start tmux again.
local use_herdr = true

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

if use_herdr then
  -- Herdr can merge a quick Escape press with its Kitty key-release event.
  config.enable_kitty_keyboard = false

  local function herdr_key(key, mods, sequence)
    return {
      key = key,
      mods = mods,
      action = wezterm.action_callback(function(window, pane)
        local process = pane:get_foreground_process_name()
        local action
        if process == 'herdr' or (process and process:match('/herdr$')) then
          action = wezterm.action.SendString(sequence)
        else
          action = wezterm.action.SendKey { key = key, mods = mods }
        end
        window:perform_action(action, pane)
      end),
    }
  end

  config.keys = {
    herdr_key('Escape', 'NONE', '\x1b[27;1u'),
  }
  for number = 1, 9 do
    table.insert(config.keys, herdr_key(
      tostring(number), 'CTRL', string.format('\x1b[%d;5u', 48 + number)
    ))
  end

  config.default_prog = { wezterm.home_dir .. '/.local/bin/herdr' }
else
  config.default_prog = { tmux_cmd, '-T 256' }
end

-- and finally, return the configuration to wezterm
return config
