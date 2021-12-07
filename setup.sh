#!/bin/bash

OS_FOLDER="osx"

case "$OSTYPE" in
  solaris*|linux*|bsd*) OS_FOLDER="linux" ;;
  darwin*) OS_FOLDER="osx" ;; 
  msys*|cygwin*) OS_FOLDER="windows" ;;
  *) OS_FOLDER="osx" ;;
esac

if [ ! -d ~/.config ]; then
    mkdir ~/.config/
fi

echo -e "Copying common .config files..."
cp -r ./common/.config/* ~/.config
echo -e "Done."

echo -e "Copying common dotfiles..."
rsync -q ./common/ ~/ 
echo -e "Done."

echo -e "Copying OS specific files..."
pushd $OS_FOLDER
./setup.sh
popd
echo -e "Done."