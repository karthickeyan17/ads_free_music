#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# Ads-Free Music - Universal Installer
# Supported: Arch Linux, Debian, Ubuntu, antiX, Termux
# ============================================================

APP_NAME="Ads-Free Music"
APP_DIR="$HOME/.local/share/music"
MPV_DIR="$HOME/.config/mpv"
MPV_CONF="$MPV_DIR/mpv.conf"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_SOURCE="$SCRIPT_DIR/music.py"

# -------------------- Output helpers -------------------------

info() {
    printf '\033[1;34m[INFO]\033[0m %s\n' "$*"
}

success() {
    printf '\033[1;32m[ OK ]\033[0m %s\n' "$*"
}

warn() {
    printf '\033[1;33m[WARN]\033[0m %s\n' "$*" >&2
}

error() {
    printf '\033[1;31m[ERROR]\033[0m %s\n' "$*" >&2
    exit 1
}

# -------------------- Detect platform ------------------------

IS_TERMUX=false

if [[ "${PREFIX:-}" == *"/com.termux/files/usr" ]] &&
   [[ -d "$PREFIX/bin" ]]; then
    IS_TERMUX=true
    BIN_DIR="$PREFIX/bin"
    info "Platform detected: Termux (Android)"
else
    BIN_DIR="$HOME/.local/bin"

    if [[ -f /etc/arch-release ]]; then
        info "Platform detected: Arch Linux"
    elif [[ -f /etc/debian_version ]]; then
        info "Platform detected: Debian/Ubuntu/antiX"
    else
        info "Platform detected: Linux"
    fi
fi

# -------------------- Find Python ---------------------------

if command -v python >/dev/null 2>&1; then
    PYTHON_CMD="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="$(command -v python3)"
else
    error "Python is missing.

Arch Linux:
  sudo pacman -S --needed python

Debian/Ubuntu/antiX:
  sudo apt update
  sudo apt install python3 python3-venv python3-pip

Termux:
  pkg update
  pkg install python"
fi

info "Python executable: $PYTHON_CMD"

# -------------------- Check system dependencies --------------

MISSING=()

for cmd in mpv fzf; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        MISSING+=("$cmd")
    fi
done

if ((${#MISSING[@]})); then
    error "Missing system dependencies: ${MISSING[*]}

Install them, then run this installer again.

Arch Linux:
  sudo pacman -S --needed mpv fzf

Debian/Ubuntu/antiX:
  sudo apt update
  sudo apt install mpv fzf

Termux:
  pkg update
  pkg install mpv fzf"
fi

# -------------------- Check application source ---------------

[[ -f "$SCRIPT_SOURCE" ]] ||
    error "music.py was not found in:
  $SCRIPT_DIR

Keep install.sh and music.py in the same directory."

# -------------------- Create directories ---------------------

mkdir -p "$APP_DIR" "$MPV_DIR"

if ! "$PYTHON_CMD" -m venv --help >/dev/null 2>&1; then
    error "Python virtual environment support is unavailable.

Debian/Ubuntu/antiX:
  sudo apt install python3-venv python3-pip

Then run this installer again."
fi

# -------------------- Create virtual environment --------------

if [[ ! -x "$APP_DIR/bin/python" ]]; then
    info "Creating Python virtual environment..."

    if ! "$PYTHON_CMD" -m venv "$APP_DIR"; then
        error "Could not create the virtual environment.

On Debian/Ubuntu/antiX, try:
  sudo apt install python3-venv python3-pip

On Termux, try:
  pkg reinstall python

Then run this installer again."
    fi
else
    info "Using existing Python virtual environment."
fi

VENV_PYTHON="$APP_DIR/bin/python"

[[ -x "$VENV_PYTHON" ]] ||
    error "Virtual environment Python was not created successfully."

# -------------------- Install Python dependencies ------------

info "Installing/updating Python dependencies..."
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install --upgrade \
    'yt-dlp[default]' \
    ytmusicapi

success "Python dependencies installed."

# -------------------- Install music.py -----------------------

info "Installing music.py..."
install -m 755 "$SCRIPT_SOURCE" "$BIN_DIR/music.py"

# -------------------- Create launcher ------------------------

info "Creating music launcher..."

if "$IS_TERMUX"; then
    cat > "$BIN_DIR/music" <<'LAUNCHER'
#!/data/data/com.termux/files/usr/bin/sh
exec "$HOME/.local/share/music/bin/python" "$PREFIX/bin/music.py" "$@"
LAUNCHER
else
    cat > "$BIN_DIR/music" <<'LAUNCHER'
#!/bin/sh
exec "$HOME/.local/share/music/bin/python" "$HOME/.local/bin/music.py" "$@"
LAUNCHER
fi

chmod 755 "$BIN_DIR/music"

success "Launcher installed at: $BIN_DIR/music"

# -------------------- Configure MPV --------------------------

PROFILE_BEGIN="# BEGIN ads-free-music profile"
PROFILE_END="# END ads-free-music profile"

if grep -Fqx "$PROFILE_BEGIN" "$MPV_CONF" 2>/dev/null; then
    if ! grep -Fqx "$PROFILE_END" "$MPV_CONF"; then
        error "The Ads-Free Music MPV profile has a start marker but no end marker in:
  $MPV_CONF

Please repair the marked section before running the installer again."
    fi

    info "Ads-Free Music MPV profile already exists; leaving it unchanged."

elif grep -Eq '^[[:space:]]*\[music\][[:space:]]*$' "$MPV_CONF" 2>/dev/null; then
    warn "An existing [music] profile was found in:
  $MPV_CONF

It was left unchanged to protect your configuration.
Check that it contains the settings shown in the README."

else
    info "Adding Ads-Free Music MPV profile..."

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

    success "MPV profile added to $MPV_CONF"
fi

# -------------------- Check executable PATH ------------------

if ! "$IS_TERMUX"; then
    case ":${PATH:-}:" in
        *":$BIN_DIR:"*)
            ;;
        *)
            warn "$BIN_DIR is not currently in PATH."

            if [[ "${SHELL:-}" == *fish ]]; then
                printf '\nAdd it to Fish with:\n'
                printf '  fish_add_path "$HOME/.local/bin"\n'
            else
                printf '\nAdd this line to your shell configuration:\n'
                printf '  export PATH="$HOME/.local/bin:$PATH"\n'
            fi

            printf 'Then restart your terminal or reload your shell.\n'
            ;;
    esac
fi

# -------------------- Verify installation --------------------

"$VENV_PYTHON" -m pip show yt-dlp >/dev/null
"$VENV_PYTHON" -m pip show ytmusicapi >/dev/null

success "$APP_NAME installed successfully!"

printf '\n'
printf 'Executable: %s/music\n' "$BIN_DIR"
printf 'Python app: %s/music.py\n' "$BIN_DIR"
printf 'Virtual environment: %s\n' "$APP_DIR"
printf 'MPV config: %s\n' "$MPV_CONF"
printf '\n'

if "$IS_TERMUX"; then
    printf 'Run the player with:\n  music\n'
else
    printf 'Run the player with:\n  music\n'
fi

printf '\n'
info "Installation complete."
