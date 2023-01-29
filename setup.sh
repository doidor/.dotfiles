#!/usr/bin/env zsh

for folder in $(ls */ | sed "s/\///g" | sed "s/://g")
do
    echo "stow $folder"
    stow -D $folder
    stow $folder
done

