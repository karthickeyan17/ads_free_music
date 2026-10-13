# Ads-Free Music

A lightweight terminal-based music player for Linux and Android (Termux), powered by Python, MPV, FZF, yt-dlp, and YouTube Music.

## Features

- Search and play music through your music player interface.
- Lightweight terminal interface using FZF.
- MPV-powered audio playback.
- Python dependencies isolated in a virtual environment.
- Automatic installation and updating of Python dependencies.
- Dedicated MPV profile for audio playback.
- User-local installation without root privileges.
- Supports Arch Linux, Debian, Ubuntu, and Termux.

## Requirements

The following system packages must be installed:

- Python 3
- MPV
- FZF
- Git

## Installation

### Arch Linux

Install the required packages:

```bash
sudo pacman -S --needed git python mpv fzf
```

Clone the repository and run the installer:

```bash
git clone YOUR_GIT_REPOSITORY_URL
cd ads_free_music
chmod +x install.sh uninstall.sh
./install.sh
```

### Debian / Ubuntu / antiX

Update package lists and install the dependencies:

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-pip mpv fzf
```

Clone the repository and install:

```bash
git clone YOUR_GIT_REPOSITORY_URL
cd ads_free_music
chmod +x install.sh uninstall.sh
./install.sh
```

If your distribution uses a separate package for Python virtual environments, make sure it is installed. Debian-based systems may require `python3-venv`.

### Termux (Android)

Install Termux packages:

```bash
pkg update
pkg install git python mpv fzf
```

Clone the repository and run the installer:

```bash
git clone YOUR_GIT_REPOSITORY_URL
cd ads_free_music
chmod +x install.sh uninstall.sh
./install.sh
```

No root access is required.

**Termux note:** MPV audio playback depends on your Termux environment and Android audio configuration. Python packages and YouTube playback should be tested on your device.

## PATH Configuration

The installed command is located at `~/.local/bin/music`.

If the installer warns that `~/.local/bin` is missing from your PATH, configure your shell.

### Fish

```fish
fish_add_path "$HOME/.local/bin"
```

### Bash

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

For Zsh, add the same `export PATH` line to `~/.zshrc`.

## Usage

Start the player:

```bash
music
```

The player uses FZF for its terminal interface and MPV for audio playback.

## Python Environment

The installer creates a dedicated virtual environment at:

```text
~/.local/share/music/
```

It installs these Python packages inside that environment:

- `yt-dlp[default]`
- `ytmusicapi`

This keeps the application's Python dependencies separate from system-managed Python packages.

## MPV Configuration

The installer adds a dedicated `[music]` profile to:

```text
~/.config/mpv/mpv.conf
```

The profile is:

```ini
[music]
profile-restore=copy
vid=no
audio-display=no
ytdl-format=bestaudio/best
cache=yes
demuxer-max-bytes=50MiB
demuxer-max-back-bytes=20MiB
demuxer-readahead-secs=5
volume=60
```

The profile configures audio-focused playback, caching, and a default volume of 60.

For the profile to apply, the application must launch MPV with `--profile=music`.

Existing MPV configuration is preserved. The installer adds the profile only when a `[music]` section is not already present.

## Update

Enter the cloned repository and run:

```bash
git pull
./install.sh
```

This updates the application script and upgrades the Python dependencies in the virtual environment.

## Uninstall

From the cloned repository, run:

```bash
./uninstall.sh
```

The uninstaller removes the installed launcher, application script, virtual environment, and the MPV profile created by the installer.

Other MPV settings are preserved.

## Installation Locations

| Path | Purpose |
|---|---|
| `~/.local/share/music/` | Python virtual environment |
| `~/.local/bin/music` | Launcher command |
| `~/.local/bin/music.py` | Application script |
| `~/.config/mpv/mpv.conf` | MPV configuration |

All paths are relative to the current user's home directory.

## Troubleshooting

### Command not found

Ensure `~/.local/bin` is in your PATH, then restart your terminal.

### Missing dependencies

Install Python, MPV, and FZF using your distribution's package manager. The installer checks for these commands but does not install system packages automatically.

### Python package installation fails

Verify that Python, pip, and virtual environment support are working:

```bash
python -m venv --help
python -m pip --version
```

On Debian-based distributions, the `python3-venv` package may be required.

### MPV profile does not apply

Verify that your application starts MPV with:

```bash
mpv --profile=music
```

The actual playback command should also pass the appropriate media URL or input arguments.

### YouTube playback fails

Update the application dependencies by running the installer again. YouTube may change its playback requirements, and network restrictions or platform-specific compatibility issues can affect playback.

## Technologies

- [Python](https://www.python.org/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ytmusicapi](https://github.com/sigma67/ytmusicapi)
- [MPV](https://mpv.io/)
- [FZF](https://github.com/junegunn/fzf)

## License

Add a `LICENSE` file to the repository before distributing the project. The MIT License is one option if you want to permit reuse, modification, and redistribution under its terms.

