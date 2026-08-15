<div align="center">

# 📺 yuki-iptv

**IPTV player with EPG support**
Community-maintained continuation of the original [liya/yuki-iptv](https://codeberg.org/liya/yuki-iptv)

[![Build Status](https://build.opensuse.org/projects/home:itachi_re/packages/yuki-iptv/badge.svg?type=default)](https://build.opensuse.org/package/show/home:itachi_re/yuki-iptv)
[![GitHub Release](https://img.shields.io/github/v/release/itachi-re/yuki-iptv)](https://github.com/itachi-re/yuki-iptv/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](./COPYING)
[![Platform](https://img.shields.io/badge/platform-Linux-lightgrey?logo=linux)](https://github.com/itachi-re/yuki-iptv)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)
[![GitHub Issues](https://img.shields.io/github/issues/itachi-re/yuki-iptv)](https://github.com/itachi-re/yuki-iptv/issues)
[![Last Commit](https://img.shields.io/github/last-commit/itachi-re/yuki-iptv)](https://github.com/itachi-re/yuki-iptv/commits)

</div>

---

## ⚠️ Project Status

> **🧪 Early Testing Phase — Expect Bugs**
>
> This fork is in its **early stages**. Core functionality works, but rough edges
> exist and things may break between releases. Bug reports are not just
> tolerated — they are actively helpful. If something doesn't work, please
> [open an issue](https://github.com/itachi-re/yuki-iptv/issues).

The original upstream repository, [`liya/yuki-iptv`](https://codeberg.org/liya/yuki-iptv)
on Codeberg, has since been **removed entirely** (as of this writing the
repository returns a 404, and its listing on [Repology](https://repology.org/project/yuki-iptv/packages)
now flags the upstream homepage as dead). This is a change from the project's
earlier "archived" status. This repository is an independent, unofficial
continuation starting from upstream's final known commit (`72a32225be`,
archived on 2025-08-27) and is maintained here going forward.

Because the original repository is gone, the commit history linked above
may also disappear if Codeberg or GitHub caches expire — anyone with a local
clone predating the removal is encouraged to open an issue or PR so we can
preserve as much of that history as possible.

> **🔒 A note on trust:** this project's name has previously been targeted by lookalike forks bundling malicious code. Before installing from anywhere, verify the commit history traces cleanly back to a known source, and prefer release artifacts published directly from **this repository** over random third-party mirrors.

---

## ✨ Features

| Category | Features |
|---|---|
| **Playlists** | M3U / M3U8 / XSPF, XTream API |
| **Streams** | UDP multicast, HTTP, HLS (M3U8) |
| **Guide** | EPG via XMLTV and JTV formats |
| **Recording** | Stream recording with hotkeys |
| **Customization** | Per-channel video settings, user agent / Referer override |
| **Integration** | MPRIS support (media keys, desktop) |
| **VOD / Series** | Group-based movie/series organisation |
| **UI** | Channel search, favorites, groups, hide channels, tech info overlay |

> ⚠️ **Disclaimer:** yuki-iptv does not provide, host, or bundle any content, playlists, or TV channels. It is a player only. Channels shown in screenshots are for demonstration purposes only.

---

## 📦 Installation

### 🦎 openSUSE Tumbleweed (OBS — Recommended)

Packages are built and published via the [Open Build Service](https://build.opensuse.org/package/show/home:itachi_re/yuki-iptv).

> **🧪 Note:** OBS packages are currently in the testing phase. The build may occasionally be broken or behind. Check the build badge at the top of this page before installing.

**One-time repository setup:**

```bash
sudo zypper addrepo \
  https://download.opensuse.org/repositories/home:/itachi_re/openSUSE_Tumbleweed/home:itachi_re.repo
sudo zypper refresh
```

**Install:**

```bash
sudo zypper install yuki-iptv
```

**Update (after a new release):**

```bash
sudo zypper refresh && sudo zypper update yuki-iptv
```

**Remove repository when no longer needed:**

```bash
sudo zypper removerepo home_itachi_re
```

Alternatively, install via YaST → Software Repositories → Add → Community Repositories, and search for `home:itachi_re`.

---

### 🎩 Fedora (COPR)

Packages are built and published via [Fedora COPR](https://copr.fedorainfracloud.org/coprs/itachi-re/yuki-iptv/).

> **🧪 Note:** COPR packages are currently in the testing phase and currently target `fedora-44-x86_64` and `fedora-43-x86_64`. If your release isn't covered yet, open an issue.

**One-time repository setup + install:**

```bash
sudo dnf copr enable itachi-re/yuki-iptv
sudo dnf install yuki-iptv
```

**Update (after a new release):**

```bash
sudo dnf update yuki-iptv
```

**Remove repository when no longer needed:**

```bash
sudo dnf copr disable itachi-re/yuki-iptv
```

---

### 🏹 Arch Linux (AUR)

yuki-iptv is available on the [AUR](https://aur.archlinux.org/packages/yuki-iptv) and builds from source using your own machine, same as any other AUR package.

**Using an AUR helper (e.g. `yay` or `paru`):**

```bash
yay -S yuki-iptv
```

**Manually, without a helper:**

```bash
git clone https://aur.archlinux.org/yuki-iptv.git
cd yuki-iptv
makepkg -si
```

**Update (after a new release):** your AUR helper's normal update flow (`yay -Syu`, `paru -Syu`, etc.) will pick it up, or repeat the manual steps above.

---

### 🔧 Running from Source

```bash
git clone https://github.com/itachi-re/yuki-iptv.git
cd yuki-iptv
# Install dependencies listed in debian/control first
# At minimum: Python 3, PyQt, mpv
python3 usr/lib/yuki-iptv/yuki-iptv.py
```

If the entry point has moved, look under `usr/lib/yuki-iptv/` for the current main script.

**Dependencies:** see `debian/control` for the authoritative list. `usr/lib/yuki-iptv/thirdparty/` vendors `mpv.py` and `xtream.py` directly rather than pulling them via pip.

---

### 🗓️ Other Platforms — Coming Eventually

> **🌍 Multiplatform support is on the roadmap.** The long-term goal is to support Windows and macOS in addition to Linux, but that is a significant undertaking and is not close to landing yet.

On the Linux side, a Debian/Ubuntu `.deb` is also **planned but not yet available**. openSUSE, Fedora, and Arch are covered above.

In the meantime, [running from source](#-running-from-source) works on any Linux distro with Python 3, PyQt, and `mpv` available. If you'd like to contribute packaging or platform support, pull requests are very welcome.

---

## 🗂️ Project Layout

```
usr/lib/yuki-iptv/
├── yuki-iptv.py          # Main entry point
├── yuki_iptv/            # Application modules (GUI, EPG, playlist, XTream, recording, MPRIS…)
└── thirdparty/           # Vendored libs: mpv.py, xtream.py (check individual license headers)
usr/bin/yuki-iptv         # Installed launcher script
usr/share/                # Desktop file, icons, assets
po/                       # Translation files (.po / .pot)
debian/                   # Debian packaging
```

---

## 📺 Making Playlists for Movies / Series (VOD)

Use the group `VOD` for movies:

```text
#EXTM3U
#EXTINF:-1 group-title="VOD",Channel 1
https://example.com
#EXTINF:-1 group-title="VOD SomeGroup",Channel 2
https://example.com
```

Use `SxxExx` in an entry's name to have it recognised as a series episode — for example `S01E12` for Season 1, Episode 12:

```text
#EXTM3U
#EXTINF:-1 tvg-name="SomeName S04E06 Season Title 1" group-title="SERIES SomeName",
file:///home/user/Videos/SomeName_4/SomeName.S04E06.mp4
```

---

## 🌐 Localization

Translation files live under `po/`. To help translate, edit the relevant `.po` file for your language and open a pull request. If a file for your language doesn't exist yet, generate one from `yuki-iptv.pot`.

---

## 🐛 Reporting Bugs

Since this fork is in early testing, **bug reports are especially valuable right now.**

Please include:
- Your distribution and version (e.g. openSUSE Tumbleweed, snapshot date)
- How you installed (OBS package / COPR / AUR / from source)
- Steps to reproduce the issue
- Any relevant log output or error messages

→ [Open an issue](https://github.com/itachi-re/yuki-iptv/issues)

---

## 📜 License

yuki-iptv is free software, licensed under the **GNU General Public License v3.0 or later**. See [`COPYING`](./COPYING) for the full license text.

yuki-iptv is based on **Astroncia IPTV**, originally licensed GPL-3.0-only. The original yuki-iptv author received permission from Astroncia's author to relicense the code as GPL-3.0-or-later — see [`LICENSE-NOTICE.txt`](./LICENSE-NOTICE.txt) for that clarification.

Font Awesome icons (Font Awesome Free 5.15.4) are licensed under CC BY 4.0 — see [`LICENSE-CC-BY-4.0.txt`](./LICENSE-CC-BY-4.0.txt).

This software is distributed **WITHOUT ANY WARRANTY**; see `COPYING` for details.

---

## 🙏 Credits

- Originally created and maintained by **[liya](https://codeberg.org/liya)**
- Based on **Astroncia IPTV**
- Continued here by **[itachi-re](https://github.com/itachi-re)** since June 2026

---

## 🤝 Contributing

Bug reports, fixes, features, and translations are all welcome.
Please read [CONTRIBUTING.md](./CONTRIBUTING.md) before opening a pull request.
