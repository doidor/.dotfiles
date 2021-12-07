#!/bin/bash

echo -e "Copying Alacrity config..."
if [ -d /mnt/c/Users/tdrpo/AppData/Roaming/alacritty ]; then
    cp ./.config/alacritty/alacritty.yml /mnt/c/Users/tdrpo/AppData/Roaming/alacritty/
elif [ -d /mnt/c/Users/doidor/AppData/Roaming/alacritty ]; then
    cp ./.config/alacritty/alacritty.yml /mnt/c/Users/doidor/AppData/Roaming/alacritty/ 
fi
echo -e "Done."

echo -e "Copying dotfiles..."
rsync -avr --exclude='setup.sh' --exclude='.config' ./ ~/ 
echo -e "Done."