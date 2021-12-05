#!/bin/bash

if [ ! -d ~/.config ]; then
    mkdir ~/.config/
fi

echo -e "Copying Alacrity config..."
if [ -d /mnt/c/Users/tdrpo/AppData/Roaming/alacritty ]; then
    cp ./.config/alacritty/alacritty.yml /mnt/c/Users/tdrpo/AppData/Roaming/alacritty/
elif [ -d /mnt/c/Users/doidor/AppData/Roaming/alacritty ]; then
    cp ./.config/alacritty/alacritty.yml /mnt/c/Users/doidor/AppData/Roaming/alacritty/ 
fi
echo -e "Done."

echo -e "Copying .config files..."
cp -r ./.config/* ~/.config
echo -e "Done."
echo -e "Copying dotfiles..."
cp ./* ~/
echo -e "Done."
