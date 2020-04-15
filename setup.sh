#!/bin/bash

DEBS_FOLDER=/tmp/debs

add-apt-repository main
add-apt-repository universe
add-apt-repository restricted
add-apt-repository multiverse

apt update

apt install -y git git-core debhelper qtbase5-dev qt5-qmake qt4-linguist-tools libqt5dbus5 libqt5svg5-dev libcrypto++-dev libraw-dev libc-ares-dev libssl-dev libsqlite3-dev zlib1g-dev wget dh-autoreconf cdbs unzip libtool-bin pkg-config qt5-default qttools5-dev-tools libavcodec-dev libavutil-dev libavformat-dev libswscale-dev libmediainfo-dev caffeine deluge build-essential terminator fzf curl zsh simplescreenrecorder

curl https://pyenv.run | bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.2/install.sh | bash
curl -sSL https://get.docker.com/ | sh
curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl

mkdir $DEBS_FOLDER

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O $DEBS_FOLDER/chrome.deb
wget https://go.microsoft.com/fwlink/?LinkID=760868 -O $DEBS_FOLDER/visualstudiocode.deb
wget https://downloads.slack-edge.com/linux_releases/slack-desktop-3.3.3-amd64.deb -O $DEBS_FOLDER/slack.deb
wget https://repo.skype.com/latest/skypeforlinux-64.deb -O $DEBS_FOLDER/skype.deb
wget https://mega.nz/linux/MEGAsync/xUbuntu_19.10/amd64/megasync-xUbuntu_19.10_amd64.deb -O $DEBS_FOLDER/megasync.deb
wget https://github.com/keeweb/keeweb/releases/download/v1.12.3/KeeWeb-1.12.3.linux.x64.deb -O $DEBS_FOLDER/keeweb.deb

dpkg -i $DEBS_FOLDER/*.deb

apt install -f -y

echo -e "\nSetup finished. You'll need to manually set oh-my-zsh now and copy the config files."