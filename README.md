## dotfiles setup

This project contains multiple setup files for Windows, Linux and MacOS. When working on Windows, I use WSL for all tools, except Alacritty.

To automatically copy all config files to their destination, run the `setup.sh` with one of the following flags (or none):

Dev notes: each os folder has its own `setup.sh` folder so os-specific customizations can be made. The os-specific setup is called after the common one does its job.

This contains my configuration files for:

- [Alacritty](https://github.com/alacritty/alacritty)
- [tmux](https://github.com/tmux/tmux)
- [zsh](https://ohmyz.sh/)
- [neovim](https://neovim.io/).

This also contains my config for the [regolith](https://regolith-linux.org/) distro with some basic tools for development.
