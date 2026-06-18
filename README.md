# yuki-iptv

IPTV player with EPG support — a community-maintained continuation of the original **yuki-iptv** project.

## ⚠️ Project status

The original upstream repository, [`liya/yuki-iptv`](https://codeberg.org/liya/yuki-iptv) on Codeberg, has been **archived by its maintainer** and is no longer being actively developed. This repository is an independent, unofficial continuation, starting from upstream's final commit (`72a32225be`, the last commit before the repository was archived on 2025-08-27) and maintained here going forward.

The full original commit history is still readable directly at the link above for anyone who wants to trace this fork's lineage back to the source.

> **A note on trust:** this project's name has previously been targeted by lookalike forks bundling unrelated or malicious code. Before installing from anywhere, check that the commit history traces back cleanly to a known source, and prefer release artifacts published directly from this repository over random third-party mirrors.

## Features

- M3U / M3U8 / XSPF playlist support
- XTream API support
- Unencrypted UDP (multicast), HTTP, and HLS (M3U8) stream playback
- TV guide / EPG support (XMLTV and JTV formats)
- Save channels as favorites
- Stream recording
- Hotkeys and channel search
- Technical info overlay (video/audio codec, bitrate, resolution)
- Channel groups (from playlist and custom)
- Hide channels
- Per-channel video settings (contrast, brightness, hue, saturation, gamma)
- Per-channel user agent / HTTP Referer override
- Built-in playlist editor
- TV archive / catchup support
- MPRIS support (media keys / desktop integration)
- ...and more — check the commit history for ongoing additions

⚠️ **Disclaimer:** yuki-iptv does not provide, host, or bundle any content, playlists, or TV channels. It is a player only. Any channels shown in screenshots are for demonstration purposes only.

## Installation

This project currently targets Debian-based Linux distributions primarily.

- **Debian/Ubuntu:** build the `.deb` package using `debian/` (e.g. `create-release-deb.sh`), or check this repo's Releases page for a prebuilt package once one exists.
- **Other distros:** there's no RPM packaging in this source tree (it was dropped upstream before this fork's starting commit) — install from source for now, or contribute packaging if you'd like to add it back.
- **Dependencies:** see `debian/control` for the authoritative list. At minimum you'll need Python 3, PyQt, and `mpv`. Note that `usr/lib/yuki-iptv/thirdparty/` vendors a couple of third-party libraries directly (`mpv.py`, `xtream.py`) rather than pulling them in via pip.

### Running from source

```bash
git clone https://github.com/itachi-re/yuki-iptv.git
cd yuki-iptv
# install the dependencies listed in debian/control first
python3 usr/lib/yuki-iptv/yuki-iptv.py
```

If the entry point has moved by the time you read this, look under `usr/lib/yuki-iptv/` for the current main script.

### Project layout

- `usr/lib/yuki-iptv/yuki-iptv.py` — main entry point
- `usr/lib/yuki-iptv/yuki_iptv/` — the actual application code, split into modules (GUI, EPG, playlist parsing, XTream, recording, MPRIS, etc.)
- `usr/lib/yuki-iptv/thirdparty/` — vendored third-party code (`mpv.py`, `xtream.py`) — these may carry their own license headers separate from the GPL, so check the files directly before redistributing modified copies
- `usr/bin/yuki-iptv` — the installed launcher script
- `usr/share/` — desktop file, icons, and other installed assets
- `po/` — translation files
- `debian/` — Debian packaging

## Making playlists for movies/series (VOD)

Use the group `VOD` for movies:

```text
#EXTM3U
#EXTINF:-1 group-title="VOD",Channel 1
https://example.com
#EXTINF:-1 group-title="VOD SomeGroup",Channel 2
https://example.com
```

Use `SxxExx` in an entry's name to have it recognized as a series episode — for example, `S01E12` for Season 1, Episode 12:

```text
#EXTM3U
#EXTINF:-1 tvg-name="SomeName S04E06 Season Title 1" group-title="SERIES SomeName",
file:///home/user/Videos/SomeName_4/SomeName.S04E06.mp4
```

## Localization

Translation files live under `po/`. To help translate, edit the relevant `.po` file for your language and open a pull request. If a file for your language doesn't exist yet, generate one from `yuki-iptv.pot`.

## License

yuki-iptv is free software, licensed under the **GNU General Public License v3.0 or later**. See [`COPYING`](./COPYING) for the full license text.

yuki-iptv is based on **Astroncia IPTV**, originally licensed GPL-3.0-only. The original yuki-iptv author received permission from Astroncia's author to relicense the code as GPL-3.0-or-later — see [`LICENSE-NOTICE.txt`](./LICENSE-NOTICE.txt) for that clarification.

Font Awesome icons (Font Awesome Free 5.15.4) used in this project are licensed under CC BY 4.0 — see [`LICENSE-CC-BY-4.0.txt`](./LICENSE-CC-BY-4.0.txt).

This software is distributed WITHOUT ANY WARRANTY; see `COPYING` for details.

## Credits

- Originally created and maintained by **liya** ([codeberg.org/liya](https://codeberg.org/liya))
- Based on **Astroncia IPTV**
- Continued here by **[itachi-re](https://github.com/itachi-re)** since June 2026

## Contributing

Bug reports, fixes, features, and translations are all welcome — see [CONTRIBUTING.md](./CONTRIBUTING.md) before opening a pull request.
