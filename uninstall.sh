#!/usr/bin/env bash
set -Eeuo pipefail

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/music"
MPV_CONF="$HOME/.config/mpv/mpv.conf"

rm -f "$BIN_DIR/music" "$BIN_DIR/music.py"
rm -rf "$APP_DIR"

# Remove only the [music] profile and its settings.
if [[ -f "$MPV_CONF" ]] &&
   grep -q '^\[music\][[:space:]]*$' "$MPV_CONF"; then

    tmp_file="$(mktemp "${MPV_CONF}.XXXXXX")"
    trap 'rm -f "$tmp_file"' EXIT

    awk '
        /^\[music\][[:space:]]*$/ {
            skip = 1
            next
        }

        /^\[/ {
            skip = 0
        }

        !skip {
            print
        }
    ' "$MPV_CONF" > "$tmp_file"

    cat "$tmp_file" > "$MPV_CONF"
    rm -f "$tmp_file"
    trap - EXIT

    printf 'Removed MPV music profile.\n'
fi

printf 'Music player uninstalled.\n'
