#!/bin/bash

echo -e "Copying dotfiles..."
rsync -avr --exclude='setup.sh' ./ ~/ 
echo -e "Done."

# echo -e "Installing dependencies..."
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# brew update
# brew install --cask visual-studio-code
# brew install tmux
# curl -L https://nixos.org/nix/install | sh
# nix-env -i neovim direnv 
# https://rectangleapp.com/
# https://alt-tab-macos.netlify.app/
# https://github.com/leits/MeetingBar
# https://github.com/alacritty/alacritty/releases