#!/usr/bin/env bash
set -Eeuo pipefail

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/music"
MPV_CONF="$HOME/.config/mpv/mpv.conf"

rm -f "$BIN_DIR/music" "$BIN_DIR/music.py"
rm -rf "$APP_DIR"

# Remove only the profile block created by this installer.
if [[ -f "$MPV_CONF" ]] &&
   grep -q '^# BEGIN ads-free-music profile$' "$MPV_CONF"; then

    tmp_file="$(mktemp "${MPV_CONF}.XXXXXX")"
    trap 'rm -f "$tmp_file"' EXIT

    awk '
        /^# BEGIN ads-free-music profile$/ {
            skip = 1
            next
        }

        /^# END ads-free-music profile$/ {
            skip = 0
            next
        }

        !skip {
            print
        }
    ' "$MPV_CONF" > "$tmp_file"

    cat "$tmp_file" > "$MPV_CONF"
    rm -f "$tmp_file"
    trap - EXIT

    printf 'Removed Ads-Free Music MPV profile.\n'
fi

printf 'Music player uninstalled.\n'
