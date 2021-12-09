#!/bin/bash

OS_FOLDER="osx"

case "$OSTYPE" in
  solaris*|linux*|bsd*)
    if grep -qi microsoft /proc/version; then
      OS_FOLDER="windows"
    else 
      OS_FOLDER="linux" 
    fi
    ;;
  darwin*) OS_FOLDER="osx" ;; 
  msys*|cygwin*) OS_FOLDER="windows" ;;
  *) OS_FOLDER="osx" ;;
esac

if [ ! -d ~/.config ]; then
    mkdir ~/.config/
fi

echo -e "Copying common dotfiles..."
rsync -avr ./common/ ~/ 
echo -e "Done."

echo -e "Copying OS specific files..."
pushd $OS_FOLDER
./setup.sh
popd
echo -e "Done."