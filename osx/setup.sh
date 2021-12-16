#!/bin/bash

echo -e "Copying dotfiles..."
rsync -avr --exclude='setup.sh' ./ ~/ 
echo -e "Done."

# echo -e "Installing dependencies..."
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# brew update
# brew install visual-studio-code
# brew install koekeishiya/formulae/yabai 
# brew install koekeishiya/formulae/skhd 
# brew install tmux
# curl -L https://nixos.org/nix/install | sh
# nix-env -i neovim direnv 

# sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
#        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'

# https://rectangleapp.com/
# https://alt-tab-macos.netlify.app/
# https://github.com/leits/MeetingBar
# https://github.com/alacritty/alacritty/releases