# Contributing to yuki-iptv

Thanks for considering contributing. This is a community-maintained continuation of the original yuki-iptv project (originally created by liya; upstream is now archived). The goal here is simple: keep the player working, fix bugs, and carry the project forward in the same spirit as the original.

## Before you start

- Check open issues first so you don't duplicate work someone else already has in progress.
- For anything nontrivial — new features, architectural changes, dependency swaps — open an issue or discussion before investing time in a PR, so we can agree on direction first.
- This fork starts from upstream's final commit (`72a32225be`), the last one before liya's repository was archived — so there's no backlog of upstream fixes to port over. If you want to see the full history that led here, it's in [liya/yuki-iptv](https://codeberg.org/liya/yuki-iptv) on Codeberg.

## Setting up a dev environment

```bash
git clone https://github.com/itachi-re/yuki-iptv.git
cd yuki-iptv
```

Install the dependencies listed in `debian/control` — this project doesn't ship a `requirements.txt`; Python dependencies are tracked alongside the Debian packaging instead. At minimum you'll need Python 3, PyQt, and `mpv`.

The actual application code lives in `usr/lib/yuki-iptv/yuki_iptv/`, split into focused modules (gui.py, epg.py, playlist*.py, xtream.py, record.py, mpris.py, and so on) — that's the first place to look when tracking down where a given feature lives. `usr/lib/yuki-iptv/thirdparty/` holds vendored copies of `mpv.py` and `xtream.py`; treat those as upstream code from elsewhere rather than this project's own, and check their headers before modifying.

Run directly from source while developing:

```bash
python3 usr/lib/yuki-iptv/yuki-iptv.py
```

## Code style

Check the `Makefile` for whatever formatting/lint targets are currently defined — the upstream project used Black for formatting and flake8 (config in `.flake8`) for linting. Run those before submitting. If a target isn't obviously available in this fork's current Makefile yet, just match the conventions already used in the file you're editing.

## Tests

Heads up: the upstream project removed its automated test suite early on, so there isn't one to run right now. In practice this means manual testing carries a lot of weight — if your change touches playback, playlist parsing, or EPG handling, actually run the app against a real or sample playlist before opening a PR. Contributions that add automated tests back are especially welcome at this stage.

## Submitting changes

1. Fork this repository and branch off the default branch, with a name that describes the change (e.g. `fix-xtream-timeout`, `add-channel-sort`).
2. Keep commits focused — one logical change per commit makes review, and future bisecting, much easier.
3. Write commit messages that explain *why* a change was made when it isn't obvious from the diff alone, not just *what* changed.
4. Open a pull request describing what changed, why, and how you tested it.
5. Be patient but persistent with review — this is a small, volunteer-run project, so turnaround may vary.

## Reporting bugs

Please include:

- What you expected to happen vs. what actually happened
- Your OS/distro, Python version, and `mpv` version
- Steps to reproduce
- Relevant log output — redact any private playlist URLs, Xtream credentials, or API keys before pasting logs anywhere public

## Reporting security issues

Please don't open a public issue for a security vulnerability (anything that could leak credentials, execute arbitrary code from a malicious playlist, etc.). Email **xanbenson99@gmail.com** directly instead, so it can be fixed before details go public.

## Translations

Translation files live under `po/`. Edit the `.po` file for your language directly and open a PR. If your language doesn't have a file yet, generate one from `yuki-iptv.pot` first.

## License of contributions

By submitting a contribution, you agree it will be licensed under this project's existing license, GPL-3.0-or-later (see `COPYING` and `LICENSE-NOTICE.txt`). If your contribution includes third-party code or assets, make sure their license is compatible with GPL-3.0-or-later and note it in your PR description.

## Code of Conduct

This project follows the guidelines in [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md). Be respectful — everyone here is contributing in their free time.
