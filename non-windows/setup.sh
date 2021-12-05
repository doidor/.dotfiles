#!/bin/bash

if [ ! -d ~/.config ]; then
    mkdir ~/.config/
fi

echo -e "Copying .config files..."
cp -r ./.config/* ~/.config
echo -e "Done."
echo -e "Copying dotfiles..."
cp ./* ~/
echo -e "Done."
