#!/bin/bash

echo -e "Copying dotfiles..."
rsync -avr --exclude='setup.sh' ./ ~/ 
echo -e "Done."