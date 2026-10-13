#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="$HOME/.local/share/music"
BIN_DIR="$HOME/.local/bin"
MPV_DIR="$HOME/.config/mpv"
MPV_CONF="$MPV_DIR/mpv.conf"

SCRIPT_SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/music.py"

# Detect Termux.
IS_TERMUX=false
if [[ "${PREFIX:-}" == *"/com.termux/files/usr" ]]; then
    IS_TERMUX=true
fi

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

# Identify platform.
if "$IS_TERMUX"; then
    info "Platform: Termux (Android)"
else
    info "Platform: Linux"
fi

# Check dependencies.
MISSING=()

for cmd in python mpv fzf; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        MISSING+=("$cmd")
    fi
done

if ((${#MISSING[@]})); then
    error "Missing: ${MISSING[*]}.
Termux: pkg install python mpv fzf
Arch Linux: sudo pacman -S --needed python mpv fzf"
fi

# Verify Python virtual environment support.
python -m venv --help >/dev/null 2>&1 ||
    error "Python venv support is unavailable."

# Check application source.
[[ -f "$SCRIPT_SOURCE" ]] ||
    error "music.py was not found beside install.sh."

# Create directories.
mkdir -p "$APP_DIR" "$BIN_DIR" "$MPV_DIR"

# Create virtual environment if necessary.
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

# Create portable launcher.
info "Creating music launcher..."
cat > "$BIN_DIR/music" <<'LAUNCHER'
#!/bin/sh
exec "$HOME/.local/share/music/bin/python" "$HOME/.local/bin/music.py" "$@"
LAUNCHER

chmod 755 "$BIN_DIR/music"

# Add the MPV profile only if it doesn't already exist.
if ! grep -q '^\[music\][[:space:]]*$' "$MPV_CONF" 2>/dev/null; then
    info "Adding MPV music profile..."

    cat >> "$MPV_CONF" <<'MPV_CONFIG'

# BEGIN ads-free-music profile
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
# END ads-free-music profile
MPV_CONFIG

    success "MPV music profile added."
else
    info "MPV [music] profile already exists; leaving it unchanged."
fi

# Check PATH.
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
        printf '\nWarning: %s is not in PATH.\n' "$BIN_DIR"

        if [[ "${SHELL:-}" == *fish ]]; then
            printf 'Run: fish_add_path "$HOME/.local/bin"\n'
        else
            printf 'Add this to your shell configuration:\n'
            printf 'export PATH="$HOME/.local/bin:$PATH"\n'
        fi
        ;;
esac

success "Music player installed successfully!"
printf '\nRun the player with:\n  music\n'
