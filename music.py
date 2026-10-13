#!/usr/bin/python

import sys
import json
import random
import subprocess
import os
import re
import tempfile
from pathlib import Path

from ytmusicapi import YTMusic


# ============================================================
# CONFIG
# ============================================================

yt = YTMusic()

BASE = Path.home() / ".config" / "music"

PLAYLIST_DIR = BASE / "playlists"
ALBUM_DIR = BASE / "albums"

PLAYLIST_DIR.mkdir(parents=True, exist_ok=True)
ALBUM_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# TERMINAL
# ============================================================

def clear_screen():
    print("\033[2J\033[H", end="", flush=True)


# ============================================================
# FZF
# ============================================================

def fzf(
    items,
    prompt="🎵 ",
    header="ENTER = Select | ESC = Back"
):

    if not items:
        return None

    p = subprocess.run(
        [
            "fzf",
            "--layout=reverse",
            "--height=90%",
            "--border=rounded",
            "--info=inline",
            "--prompt=" + prompt,
            "--header=" + header,
            "--no-multi",
            "--cycle",
        ],
        input="\n".join(items),
        text=True,
        stdout=subprocess.PIPE,
    )

    value = p.stdout.strip()

    return value if value else None


# ============================================================
# FILE HELPERS
# ============================================================

def clean_name(name):

    for c in '/\\:*?"<>|':
        name = name.replace(c, "_")

    return name.strip() or "Playlist"


def path_for(name):

    return PLAYLIST_DIR / (
        clean_name(name) + ".json"
    )


def album_path_for(name):

    return ALBUM_DIR / (
        clean_name(name) + ".json"
    )


# ============================================================
# LOCAL PLAYLISTS
# ============================================================

def load_local(name):

    path = path_for(name)

    if not path.exists():
        return {
            "name": name,
            "songs": []
        }

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return {
            "name": name,
            "songs": []
        }


def save_local(data):

    path = path_for(
        data["name"]
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def local_names():

    names = []

    for p in sorted(
        PLAYLIST_DIR.glob("*.json")
    ):

        try:

            data = json.loads(
                p.read_text(
                    encoding="utf-8"
                )
            )

            if data.get("name"):
                names.append(
                    data["name"]
                )

        except Exception:
            pass

    return names


# ============================================================
# LOCAL ALBUMS
# ============================================================

def load_album(name):

    path = album_path_for(name)

    if not path.exists():
        return {
            "name": name,
            "songs": []
        }

    try:

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        return {
            "name": name,
            "songs": []
        }


def save_album_data(data):

    path = album_path_for(
        data["name"]
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def local_album_names():

    names = []

    for p in sorted(
        ALBUM_DIR.glob("*.json")
    ):

        try:

            data = json.loads(
                p.read_text(
                    encoding="utf-8"
                )
            )

            if data.get("name"):
                names.append(
                    data["name"]
                )

        except Exception:
            pass

    return names


# ============================================================
# SONG FORMAT
# ============================================================

def song_from_result(x):

    if not isinstance(x, dict):
        return None

    video_id = x.get("videoId")

    if not video_id:
        return None

    artists = x.get(
        "artists"
    ) or []

    artist = ", ".join(
        a.get("name", "")
        for a in artists
        if a.get("name")
    )

    album = x.get(
        "album"
    ) or {}

    if isinstance(album, dict):

        album_name = album.get(
            "name",
            ""
        )

    else:

        album_name = str(album)

    return {
        "videoId": video_id,
        "title": x.get(
            "title",
            "Unknown"
        ),
        "artists": artist,
        "album": album_name,
    }


# ============================================================
# PLAYBACK
# ============================================================

def youtube_url(video_id):
    """Build the normal YouTube watch URL from a video ID."""
    if not video_id:
        return None

    video_id = str(video_id).strip()

    # If an old playlist entry accidentally contains a full YouTube URL,
    # recover just the video ID. New entries should contain only videoId.
    match = re.search(r"(?:v=|youtu\.be/|youtube\.com/watch/)([A-Za-z0-9_-]{11})", video_id)
    if match:
        video_id = match.group(1)

    return f"https://youtube.com/watch?v={video_id}"


def play_one(song):

    video_id = song.get("videoId")
    url = youtube_url(video_id)

    if not url:
        print("\n❌ Song has no YouTube video ID.")
        input("Press Enter...")
        return

    env = os.environ.copy()

    env["MUSIC_TITLE"] = song.get("title", "Unknown")
    env["MUSIC_ARTIST"] = song.get("artists", "Unknown Artist")
    env["MUSIC_ALBUM"] = song.get("album", "Unknown Album")

    result = subprocess.run(
        [
            "mpv",
            "--profile=music",
            url
        ],
        env=env
    )

    if result.returncode == 42:
        raise SystemExit(42)

    return result.returncode


def play_queue(
    songs,
    shuffle=False
):

    if not songs:

        print(
            "\n❌ Playlist is empty."
        )

        input(
            "Press Enter..."
        )

        return

    queue = list(songs)

    if shuffle:
        random.shuffle(queue)

    playlist_file = None
    metadata_file = None

    try:

        playlist = []
        metadata = []

        for song in queue:

            url = youtube_url(song.get("videoId"))

            if not url:
                continue

            playlist.append(url)

            metadata.append({
                "title": song.get("title", "Unknown"),
                "artists": song.get(
                    "artists",
                    "Unknown Artist"
                ),
                "album": song.get(
                    "album",
                    "Unknown Album"
                )
            })

        playlist_tmp = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".m3u",
            delete=False
        )

        metadata_tmp = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            delete=False
        )

        playlist_file = playlist_tmp.name
        metadata_file = metadata_tmp.name

        playlist_tmp.write(
            "\n".join(playlist)
        )

        playlist_tmp.close()

        json.dump(
            metadata,
            metadata_tmp,
            ensure_ascii=False
        )

        metadata_tmp.close()

        env = os.environ.copy()
        env["MUSIC_QUEUE_META"] = metadata_file

        clear_screen()

        result = subprocess.run(
            [
                "mpv",
                "--profile=music",
                "--playlist=" + playlist_file
            ],
            env=env
        )

        if result.returncode == 42:
            raise SystemExit(42)

    finally:

        if playlist_file:
            try:
                os.unlink(playlist_file)
            except OSError:
                pass

        if metadata_file:
            try:
                os.unlink(metadata_file)
            except OSError:
                pass

    clear_screen()


# ============================================================
# SEARCH SONGS
# ============================================================

def search_songs(query):

    try:

        results = yt.search(
            query,
            filter="songs",
            limit=20
        )

    except Exception as e:

        print(
            f"\n❌ Search failed:\n{e}"
        )

        input(
            "Press Enter..."
        )

        return

    songs = []
    items = []

    for i, result in enumerate(
        results,
        1
    ):

        song = song_from_result(
            result
        )

        if not song:
            continue

        songs.append(song)

        items.append(
            f"{i:02d}  "
            f"{song['title']}"
            f"  —  "
            f"{song['artists']}"
            f"\t{i-1}"
        )

    selected = fzf(
        items,
        prompt="🎵 ",
        header=(
            "SONGS • "
            "ENTER = Select | ESC = Back"
        )
    )

    if not selected:
        return

    index = int(
        selected.rsplit(
            "\t",
            1
        )[-1]
    )

    if index >= len(songs):
        return

    song_actions(
        songs[index]
    )


# ============================================================
# SONG ACTIONS
# ============================================================

def song_actions(song):

    action = fzf(
        [
            "▶  Play",
            "➕  Add to Local Playlist",
        ],
        prompt="🎵 ",
        header=(
            f"{song['title']} • ACTIONS"
        )
    )

    if not action:
        return

    if action.startswith("▶"):

        play_one(song)

    elif action.startswith("➕"):

        add_song(song)


# ============================================================
# ADD SONG
# ============================================================

def add_song(song):

    names = local_names()

    items = [
        f"📋  {name}\t{name}"
        for name in names
    ]

    items.append(
        "➕  Create Playlist"
    )

    selected = fzf(
        items,
        prompt="➕ ",
        header="ADD TO PLAYLIST"
    )

    if not selected:
        return

    if selected.startswith("➕"):

        name = input(
            "\nNew playlist name: "
        ).strip()

        if not name:
            return

        data = {
            "name": name,
            "songs": []
        }

    else:

        name = selected.rsplit(
            "\t",
            1
        )[-1]

        data = load_local(name)

    songs = data.setdefault(
        "songs",
        []
    )

    if any(
        s.get("videoId") == song.get(
            "videoId"
        )
        for s in songs
    ):

        print(
            "\n⚠️ Already in playlist."
        )

        input(
            "Press Enter..."
        )

        return

    songs.append(song)

    save_local(data)

    print(
        f"\n✓ Added to {data['name']}"
    )

    input(
        "Press Enter..."
    )


# ============================================================
# SEARCH PLAYLISTS
# ============================================================

def search_playlists(query):

    try:

        results = yt.search(
            query,
            filter="playlists",
            limit=15
        )

    except Exception as e:

        print(
            f"\n❌ Playlist search failed:"
            f"\n{e}"
        )

        input(
            "Press Enter..."
        )

        return

    items = []

    for result in results:

        browse = result.get(
            "browseId"
        )

        playlist_id = result.get(
            "playlistId"
        )

        if not playlist_id:

            if browse and browse.startswith(
                "VL"
            ):

                playlist_id = browse[2:]

            else:

                playlist_id = browse

        if not playlist_id:
            continue

        title = result.get(
            "title",
            "Unknown Playlist"
        )

        author = result.get(
            "author",
            ""
        )

        count = result.get(
            "itemCount",
            ""
        )

        suffix = ""

        if count:
            suffix = (
                f" • {count} songs"
            )

        items.append(
            f"📋  {title}"
            f"  —  {author}"
            f"{suffix}"
            f"\t{playlist_id}"
            f"\t{title}"
        )

    selected = fzf(
        items,
        prompt="📋 ",
        header=(
            "PLAYLISTS • "
            "ENTER = Open | ESC = Back"
        )
    )

    if not selected:
        return

    parts = selected.split(
        "\t"
    )

    if len(parts) < 3:
        return

    playlist_id = parts[1]
    title = parts[2]

    playlist_actions(
        playlist_id,
        title
    )


# ============================================================
# YOUTUBE PLAYLIST ACTIONS
# ============================================================

def playlist_actions(
    playlist_id,
    title
):

    action = fzf(
        [
            "▶  Play",
            "💾  Save Whole Playlist",
        ],
        prompt="📋 ",
        header=(
            f"{title} • ACTIONS"
        )
    )

    if not action:
        return

    if action.startswith("▶"):

        print(
            f"\n⏳ Loading playlist: "
            f"{title}"
        )

        data = fetch_playlist(
            playlist_id,
            title
        )

        if data:

            play_queue(
                data["songs"]
            )

    elif action.startswith("💾"):

        save_whole_playlist(
            playlist_id,
            title
        )


# ============================================================
# FETCH WHOLE PLAYLIST
# ============================================================

def fetch_playlist(
    playlist_id,
    fallback_title
):

    try:

        result = yt.get_playlist(
            playlist_id,
            limit=None
        )

    except Exception as e:

        print(
            f"\n❌ Playlist fetch failed:"
            f"\n{e}"
        )

        input(
            "Press Enter..."
        )

        return None

    title = result.get(
        "title",
        fallback_title
    )

    tracks = result.get(
        "tracks",
        []
    )

    songs = []

    for track in tracks:

        song = song_from_result(
            track
        )

        if song:
            songs.append(song)

    return {
        "name": title,
        "source": "youtube_music",
        "playlist_id": playlist_id,
        "songs": songs
    }


# ============================================================
# SAVE WHOLE PLAYLIST
# ============================================================

def save_whole_playlist(
    playlist_id,
    title
):

    print()
    print(
        "💾 Saving playlist..."
    )
    print(
        f"📋 {title}"
    )
    print(
        "⏳ Fetching songs..."
    )

    data = fetch_playlist(
        playlist_id,
        title
    )

    if not data:
        return

    name = data["name"]

    existing = path_for(name)

    if existing.exists():

        answer = input(
            f'\n"{name}" already exists.'
            f' Replace it? [y/N]: '
        ).strip().lower()

        if answer != "y":
            return

    save_local(data)

    print()
    print(
        f"✓ Saved: {name}"
    )
    print(
        f"🎵 {len(data['songs'])} songs"
    )

    input(
        "\nPress Enter..."
    )


# ============================================================
# ALBUM SEARCH
# ============================================================

def search_albums(query):

    try:

        results = yt.search(
            query,
            filter="albums",
            limit=20
        )

    except Exception as e:

        print(
            f"\n❌ Album search failed:"
            f"\n{e}"
        )

        input(
            "Press Enter..."
        )

        return

    albums = []
    items = []

    for i, result in enumerate(
        results,
        1
    ):

        browse_id = result.get(
            "browseId"
        )

        if not browse_id:
            continue

        title = result.get(
            "title",
            "Unknown Album"
        )

        artists = result.get(
            "artists"
        ) or []

        artist = ", ".join(
            a.get("name", "")
            for a in artists
            if a.get("name")
        )

        year = result.get(
            "year",
            ""
        )

        albums.append({
            "browseId": browse_id,
            "title": title,
            "artist": artist
        })

        suffix = ""

        if year:
            suffix = f" • {year}"

        items.append(
            f"{i:02d}  💿 {title}"
            f"  —  {artist}"
            f"{suffix}"
            f"\t{i-1}"
        )

    if not items:

        print(
            "\n❌ No albums found."
        )

        input(
            "Press Enter..."
        )

        return

    selected = fzf(
        items,
        prompt="💿 ",
        header=(
            "ALBUMS • "
            "ENTER = Open | ESC = Back"
        )
    )

    if not selected:
        return

    index = int(
        selected.rsplit(
            "\t",
            1
        )[-1]
    )

    if index >= len(albums):
        return

    album = albums[index]

    open_album(
        album["browseId"],
        album["title"],
        album["artist"]
    )


# ============================================================
# OPEN ALBUM
# ============================================================

def open_album(
    browse_id,
    title,
    artist
):

    try:

        result = yt.get_album(
            browse_id
        )

    except Exception as e:

        print(
            f"\n❌ Failed to load album:"
            f"\n{e}"
        )

        input(
            "Press Enter..."
        )

        return

    songs = []

    for track in result.get(
        "tracks",
        []
    ):

        song = song_from_result(
            track
        )

        if song:
            songs.append(song)

    if not songs:

        print(
            "\n❌ No songs found in album."
        )

        input(
            "Press Enter..."
        )

        return

    while True:

        action = fzf(
            [
                "▶  Play All",
                "🔀 Shuffle",
                "💾 Save Album",
                "🎵 Browse Songs",
            ],
            prompt="💿 ",
            header=(
                f"{title} • "
                f"{len(songs)} songs • "
                "ENTER = Select | ESC = Back"
            )
        )

        if not action:
            return

        if action.startswith("▶"):

            play_queue(
                songs,
                shuffle=False
            )

        elif action.startswith("🔀"):

            play_queue(
                songs,
                shuffle=True
            )

        elif action.startswith("💾"):

            save_album(
                title,
                artist,
                songs
            )

        elif action.startswith("🎵"):

            browse_album_songs(
                title,
                songs
            )


# ============================================================
# SAVE ALBUM
# ============================================================

def save_album(
    title,
    artist,
    songs
):

    if not songs:

        print(
            "\n❌ Album is empty."
        )

        input(
            "Press Enter..."
        )

        return

    name = (
        title.strip()
        or "Album"
    )

    existing = album_path_for(
        name
    )

    if existing.exists():

        answer = input(
            f'\n"{name}" already exists.'
            f' Replace it? [y/N]: '
        ).strip().lower()

        if answer != "y":
            return


# ============================================================
# COMPLETE SAVE ALBUM
# ============================================================

def save_album(
    title,
    artist,
    songs
):

    if not songs:
        print("\n❌ Album is empty.")
        input("Press Enter...")
        return

    name = title.strip() or "Album"

    existing = album_path_for(name)

    if existing.exists():

        answer = input(
            f'\n"{name}" already exists.'
            f' Replace it? [y/N]: '
        ).strip().lower()

        if answer != "y":
            return

    data = {
        "name": name,
        "artist": artist,
        "songs": songs
    }

    save_album_data(data)

    print()
    print(f"✓ Saved album: {name}")
    print(f"🎵 {len(songs)} songs")

    input("\nPress Enter...")


# ============================================================
# BROWSE ALBUM SONGS
# ============================================================

def browse_album_songs(title, songs):

    items = []

    for i, song in enumerate(songs, 1):

        items.append(
            f"{i:02d}  {song.get('title', 'Unknown')}"
            f"  —  {song.get('artists', 'Unknown Artist')}"
            f"\t{i-1}"
        )

    selected = fzf(
        items,
        prompt="🎵 ",
        header=(
            f"{title} • {len(songs)} songs • "
            "ENTER = Select | ESC = Back"
        )
    )

    if not selected:
        return

    try:
        index = int(
            selected.rsplit("\t", 1)[-1]
        )
    except ValueError:
        return

    if 0 <= index < len(songs):
        song_actions(songs[index])


# ============================================================
# LOCAL PLAYLIST
# ============================================================

def open_local_playlist(name):

    data = load_local(name)
    songs = data.get("songs", [])

    while True:

        action = fzf(
            [
                "▶  Play All",
                "🔀 Shuffle",
                "🎵 Browse Songs",
                "➕ Add Song",
                "🗑  Delete Playlist",
            ],
            prompt="📋 ",
            header=(
                f"{name} • {len(songs)} songs • "
                "ENTER = Select | ESC = Back"
            )
        )

        if not action:
            return

        if action.startswith("▶"):

            play_queue(songs, shuffle=False)

        elif action.startswith("🔀"):

            play_queue(songs, shuffle=True)

        elif action.startswith("🎵"):

            browse_album_songs(name, songs)

        elif action.startswith("➕"):

            query = input("\nSearch song: ").strip()

            if query:
                search_songs(query)

            data = load_local(name)
            songs = data.get("songs", [])

        elif action.startswith("🗑"):

            answer = input(
                f'\nDelete "{name}"? [y/N]: '
            ).strip().lower()

            if answer == "y":

                try:
                    path_for(name).unlink()
                except FileNotFoundError:
                    pass

                print("\n✓ Playlist deleted.")
                input("Press Enter...")
                return


# ============================================================
# LOCAL PLAYLISTS
# ============================================================

def browse_local_playlists():

    while True:

        names = local_names()

        if not names:

            print("\n📋 No local playlists.")
            print("Use Search Songs → Add to Local Playlist.")
            input("\nPress Enter...")
            return

        items = [
            f"📋  {name}\t{name}"
            for name in names
        ]

        selected = fzf(
            items,
            prompt="📋 ",
            header=(
                "LOCAL PLAYLISTS • "
                "ENTER = Open | ESC = Back"
            )
        )

        if not selected:
            return

        name = selected.rsplit("\t", 1)[-1]

        open_local_playlist(name)


# ============================================================
# LOCAL ALBUM
# ============================================================

def open_local_album(name):

    data = load_album(name)
    songs = data.get("songs", [])

    if not songs:
        print("\n❌ Album is empty.")
        input("Press Enter...")
        return

    while True:

        action = fzf(
            [
                "▶  Play All",
                "🔀 Shuffle",
                "🎵 Browse Songs",
                "🗑  Delete Album",
            ],
            prompt="💿 ",
            header=(
                f"{name} • {len(songs)} songs • "
                "ENTER = Select | ESC = Back"
            )
        )

        if not action:
            return

        if action.startswith("▶"):

            play_queue(songs, shuffle=False)

        elif action.startswith("🔀"):

            play_queue(songs, shuffle=True)

        elif action.startswith("🎵"):

            browse_album_songs(name, songs)

        elif action.startswith("🗑"):

            answer = input(
                f'\nDelete album "{name}"? [y/N]: '
            ).strip().lower()

            if answer == "y":

                try:
                    album_path_for(name).unlink()
                except FileNotFoundError:
                    pass

                print("\n✓ Album deleted.")
                input("Press Enter...")
                return


# ============================================================
# LOCAL ALBUMS
# ============================================================

def browse_local_albums():

    while True:

        names = local_album_names()

        if not names:

            print("\n💿 No saved albums.")
            input("Press Enter...")
            return

        items = [
            f"💿  {name}\t{name}"
            for name in names
        ]

        selected = fzf(
            items,
            prompt="💿 ",
            header=(
                "LOCAL ALBUMS • "
                "ENTER = Open | ESC = Back"
            )
        )

        if not selected:
            return

        name = selected.rsplit("\t", 1)[-1]

        open_local_album(name)


# ============================================================
# ARTIST SEARCH
# ============================================================

def search_artists(query):

    try:

        results = yt.search(
            query,
            filter="artists",
            limit=15
        )

    except Exception as e:

        print(
            f"\n❌ Artist search failed:\n{e}"
        )

        input("Press Enter...")
        return

    artists = []
    items = []

    for i, result in enumerate(results, 1):

        browse_id = result.get("browseId")

        if not browse_id:
            continue

        name = result.get(
            "artist",
            result.get("title", "Unknown Artist")
        )

        artists.append({
            "browseId": browse_id,
            "name": name
        })

        items.append(
            f"{i:02d}  👤 {name}\t{i-1}"
        )

    if not items:

        print("\n❌ No artists found.")
        input("Press Enter...")
        return

    selected = fzf(
        items,
        prompt="👤 ",
        header=(
            "ARTISTS • "
            "ENTER = Open | ESC = Back"
        )
    )

    if not selected:
        return

    try:
        index = int(
            selected.rsplit("\t", 1)[-1]
        )
    except ValueError:
        return

    if not (0 <= index < len(artists)):
        return

    open_artist(
        artists[index]["browseId"],
        artists[index]["name"]
    )


# ============================================================
# OPEN ARTIST
# ============================================================

def open_artist(browse_id, name):

    try:

        result = yt.get_artist(browse_id)

    except Exception as e:

        print(
            f"\n❌ Failed to load artist:\n{e}"
        )

        input("Press Enter...")
        return

    songs = []

    for song_data in (
        result.get("songs", {})
        .get("results", [])
        if isinstance(result.get("songs"), dict)
        else []
    ):

        song = song_from_result(song_data)

        if song:
            songs.append(song)

    if not songs:

        print("\n❌ No songs found for artist.")
        input("Press Enter...")
        return

    while True:

        action = fzf(
            [
                "▶  Play Songs",
                "🔀 Shuffle",
                "🎵 Browse Songs",
            ],
            prompt="👤 ",
            header=(
                f"{name} • {len(songs)} songs • "
                "ENTER = Select | ESC = Back"
            )
        )

        if not action:
            return

        if action.startswith("▶"):

            play_queue(songs, shuffle=False)

        elif action.startswith("🔀"):

            play_queue(songs, shuffle=True)

        elif action.startswith("🎵"):

            browse_album_songs(name, songs)


# ============================================================
# SEARCH INPUT
# ============================================================

def ask_search():

    query = input("\nSearch: ").strip()

    return query


# ============================================================
# MAIN MENU
# ============================================================

def main():

    while True:

        clear_screen()

        action = fzf(
            [
                "🎵  Search Songs",
                "💿  Search Albums",
                "👤  Search Artists",
                "📋  Search Playlists",
                "📁  Local Playlists",
                "💿  Saved Albums",
                "🚪  Exit",
            ],
            prompt="🎶 ",
            header=(
                "MUSIC • "
                "ENTER = Select | ESC = Exit"
            )
        )

        if not action:
            clear_screen()
            return

        if action.startswith("🎵"):

            query = ask_search()

            if query:
                search_songs(query)

        elif action.startswith("💿"):

            if "Search Albums" in action:

                query = ask_search()

                if query:
                    search_albums(query)

            else:

                browse_local_albums()

        elif action.startswith("👤"):

            query = ask_search()

            if query:
                search_artists(query)

        elif action.startswith("📋"):

            query = ask_search()

            if query:
                search_playlists(query)

        elif action.startswith("📁"):

            browse_local_playlists()

        elif action.startswith("🚪"):

            clear_screen()
            return


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:

        clear_screen()

    except SystemExit:

        raise
