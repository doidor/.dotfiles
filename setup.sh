#!/bin/bash

OS_FOLDER="non-windows"

while getopts nw flag
do
    case "${flag}" in
        w) OS_FOLDER="windows";; 
        n) OS_FOLDER="non-windows";; 
    esac
done

if [ ! -d ~/.config ]; then
    mkdir ~/.config/
fi

echo -e "Copying common .config files..."
cp -r ./common/.config/* ~/.config
echo -e "Done."

echo -e "Copying common dotfiles..."
cp ./common/.* ~/
echo -e "Done."

echo -e "Copying OS specific files..."
pushd $OS_FOLDER
./setup.sh
popd
echo -e "Done."