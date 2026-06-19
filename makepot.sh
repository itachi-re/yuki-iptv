#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$(realpath "$0")")" || exit 1
echo "Creating .pot file..."
xgettext --language=Python --keyword=_ --package-name=yuki-iptv --output=yuki-iptv.pot usr/lib/yuki-iptv/yuki-iptv.py usr/lib/yuki-iptv/yuki_iptv/*.py
sed -i \
        -e 's/^# SOME DESCRIPTIVE TITLE./# yuki-iptv - IPTV player with EPG support/' \
        -e "/^# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER/d" \
        -e '/^# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR./d' \
        yuki-iptv.pot
echo "Updating .po files..."
find po -type f -name '*.po' -exec msgmerge -U -N "{}" ./yuki-iptv.pot \;
find po -type f -name '*.po~' -delete
