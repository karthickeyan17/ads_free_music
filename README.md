# Ads-Free Music

A lightweight terminal-based music player for Linux, powered by Python, MPV, FZF, yt-dlp, and YouTube Music.

## Features

- Search and play music from YouTube Music.
- Lightweight terminal interface using FZF.
- MPV-powered audio playback.
- Python dependencies isolated in a virtual environment.
- Automatic installation of required Python packages.
- Dedicated MPV profile for music playback.
- User-local installation without root privileges.
- Works with Fish, Bash, and other shells.

## Requirements

Install these system dependencies before running the installer:

- Python 3 with virtual environment support
- MPV
- FZF
- Git

### Arch Linux

```bash
sudo pacman -S --needed python mpv fzf git
```

## Installation

Clone the repository:

```bash
git clone YOUR_GIT_REPOSITORY_URL
cd ads_free_music
```

Run the installer:

```bash
chmod +x install.sh
./install.sh
```

The installer will:

1. Check whether Python, MPV, and FZF are available.
2. Create a virtual environment at `~/.local/share/music`.
3. Install `yt-dlp[default]` and `ytmusicapi` in that environment.
4. Copy `music.py` to `~/.local/bin/music.py`.
5. Create the `music` launcher in `~/.local/bin`.
6. Add the dedicated `[music]` profile to `~/.config/mpv/mpv.conf` if it doesn't already exist.

No root privileges are required, provided the system dependencies are installed.

## PATH Configuration

If the installer reports that `~/.local/bin` is not in your PATH, configure your shell.

### Fish

```fish
fish_add_path "$HOME/.local/bin"
```

### Bash

Add this line to `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Restart your terminal or reload your shell configuration.

## Usage

Start the music player:

```bash
music
```

The application uses FZF for its terminal interface and MPV for audio playback.

## MPV Configuration

The installer adds the following profile to `~/.config/mpv/mpv.conf`:

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

These settings configure MPV for audio-focused playback with caching and a default volume of 60.

For this profile to take effect, the application must launch MPV with `--profile=music`.

Existing MPV settings are preserved. The installer does not append the profile again if a `[music]` section already exists.

## Update

To update the player, enter the cloned repository and run:

```bash
git pull
./install.sh
```

The installer refreshes the application script and updates the Python dependencies in the virtual environment.

## Uninstall

Run the uninstall script from the repository:

```bash
./uninstall.sh
```

This removes the installed launcher, Python script, and virtual environment.

**Note:** If you use the original uninstall script, it does not remove the `[music]` profile from your MPV configuration. You can remove that section manually if you no longer need it.

## Installation Locations

| Path | Purpose |
|---|---|
| `~/.local/share/music/` | Python virtual environment |
| `~/.local/bin/music` | Command-line launcher |
| `~/.local/bin/music.py` | Music player application |
| `~/.config/mpv/mpv.conf` | MPV configuration |

All installation paths use `$HOME`, so the installer does not depend on a specific Linux username.

## Technologies

- Python
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ytmusicapi](https://github.com/sigma67/ytmusicapi)
- [MPV](https://mpv.io/)
- [FZF](https://github.com/junegunn/fzf)

## License

Choose a license for your project before distributing it publicly. If you want others to use, modify, and redistribute your code, consider the MIT License.

