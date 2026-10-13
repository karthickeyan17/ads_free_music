#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="$HOME/.local/share/music"
BIN_DIR="$HOME/.local/bin"
MPV_DIR="$HOME/.config/mpv"
MPV_CONF="$MPV_DIR/mpv.conf"

SCRIPT_SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/music.py"

info() {
    printf '\033[1;34m[INFO]\033[0m %s\n' "$*"
}

success() {
    printf '\033[1;32m[ OK ]\033[0m %s\n' "$*"
}

error() {
    printf '\033[1;31m[ERROR]\033[0m %s\n' "$*" >&2
    exit 1
}

# Check system dependencies.
for cmd in python fzf mpv; do
    command -v "$cmd" >/dev/null 2>&1 ||
        error "Missing dependency: $cmd. Install it and retry."
done

# Check Python venv support.
python -m venv --help >/dev/null 2>&1 ||
    error "Python venv support is unavailable."

# Check application source.
[[ -f "$SCRIPT_SOURCE" ]] ||
    error "music.py was not found in the repository."

# Create directories.
mkdir -p "$APP_DIR" "$BIN_DIR" "$MPV_DIR"

# Create the virtual environment.
if [[ ! -x "$APP_DIR/bin/python" ]]; then
    info "Creating Python virtual environment..."
    python -m venv "$APP_DIR"
else
    info "Using existing Python virtual environment."
fi

# Install Python dependencies.
info "Installing Python dependencies..."
"$APP_DIR/bin/python" -m pip install --upgrade \
    'yt-dlp[default]' ytmusicapi

# Install application.
info "Installing music.py..."
install -m 755 "$SCRIPT_SOURCE" "$BIN_DIR/music.py"

# Create launcher.
info "Creating music launcher..."
cat > "$BIN_DIR/music" <<'LAUNCHER'
#!/bin/sh
exec "$HOME/.local/share/music/bin/python" "$HOME/.local/bin/music.py" "$@"
LAUNCHER

chmod 755 "$BIN_DIR/music"

# Add MPV profile without replacing existing settings.
if ! grep -q '^\[music\][[:space:]]*$' "$MPV_CONF" 2>/dev/null; then
    info "Adding MPV music profile..."

    cat >> "$MPV_CONF" <<'MPV_CONFIG'

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
MPV_CONFIG

    success "MPV music profile added."
else
    info "MPV music profile already exists; leaving it unchanged."
fi

# PATH check.
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
        printf '\nWarning: %s is not in your PATH.\n' "$BIN_DIR"
        printf 'For Fish, run: fish_add_path "$HOME/.local/bin"\n'
        printf 'For Bash, add this to ~/.bashrc:\n'
        printf 'export PATH="$HOME/.local/bin:$PATH"\n'
        ;;
esac

success "Music player installed successfully!"
printf '\nRun your player with:\n  music\n'/ads_free_music $ cat uninstall.sh
#!/usr/bin/env bash
set -Eeuo pipefail

rm -f "$HOME/.local/bin/music" \
      "$HOME/.local/bin/music.py"

rm -rf "$HOME/.local/share/music"

printf 'Music player uninstalled.\n'

