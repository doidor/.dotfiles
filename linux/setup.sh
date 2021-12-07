#!/bin/bash

echo -e "Copying .config files..."
cp -r ./.config/* ~/.config
echo -e "Done."

echo -e "Copying dotfiles..."
rsync -avr --exclude='setup.sh' --exclude='.config' ./ ~/ 
echo -e "Done."