#!/usr/bin/env zsh

for folder in */
do
    echo "stow $folder"
    stow -D $folder
    stow $folder
done

