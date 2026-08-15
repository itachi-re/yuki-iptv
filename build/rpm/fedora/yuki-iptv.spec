#
# spec file for package yuki-iptv (Fedora)
#
# Copyright (c) 2026 itachi-re <https://github.com/itachi-re>
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

%global appdir  %{_prefix}/lib/%{name}
%global gittag  v%{version}

Name:           yuki-iptv
Version:        260813.1
Release:        1%{?dist}
Summary:        IPTV player with EPG support

# Fedora requires SPDX identifiers; this string is already SPDX-valid.
License:        GPL-3.0-or-later AND CC-BY-4.0
URL:            https://github.com/itachi-re/yuki-iptv

# GitHub strips the leading "v" from the tag when naming the top-level
# directory of the tarball, so the extracted dir is %%{name}-%%{version}
# and %%autosetup needs no -n override.
Source0:        %{url}/archive/refs/tags/%{gittag}/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  make
BuildRequires:  gettext
BuildRequires:  desktop-file-utils
BuildRequires:  hicolor-icon-theme
BuildRequires:  python3-devel

# NOTE: plain "ffmpeg" is not in Fedora's official repos (patent/codec
# policy) -- it comes from RPM Fusion. That's expected/fine for a COPR
# build, same as it would be for any other IPTV/media player. Swap to
# ffmpeg-free only if you specifically want to stay inside official
# Fedora repos, but be aware it drops H.264/AAC decode, which most IPTV
# streams need.
%if 0%{?rhel} == 9
Requires:       python3.11 >= 3.11
%else
Requires:       python3 >= 3.11
%endif
Requires:       ffmpeg
Requires:       python3-pyqt6
Requires:       python3-chardet
Requires:       python3-gobject
Requires:       python3-requests

%description
yuki-iptv is an IPTV player with M3U/M3U8/XSPF playlist support, the
XTream API, TV guide (EPG) support for XMLTV and JTV formats, stream
recording, a built-in playlist editor, TV archive/catchup, MPRIS
integration, and per-channel video and network settings.

This package builds the %{url} fork. The original upstream project,
liya/yuki-iptv on Codeberg, was archived by its maintainer on
2025-08-27; this fork is an independent, unofficial continuation
starting from upstream's last commit. yuki-iptv does not provide,
host, or bundle any playlists or TV channels -- it is a player only.

%prep
%autosetup -p1

%build
make buildmo
# Bake the package version into the About dialog / --version output, mirroring
# what debian/rules does for __DEB_VERSION__ at install time. Keep the "v"
# prefix here so the displayed version matches the git tag / RPM job
# convention used elsewhere in the release pipeline.
sed -i 's/__DEB_VERSION__/%{gittag}/' usr/lib/%{name}/%{name}.py

%install
install -Dm0755 usr/bin/%{name} %{buildroot}%{_bindir}/%{name}
mkdir -p %{buildroot}%{appdir}
cp -a usr/lib/%{name}/. %{buildroot}%{appdir}/
install -Dm0644 usr/share/applications/%{name}.desktop \
    %{buildroot}%{_datadir}/applications/%{name}.desktop
install -Dm0644 usr/share/icons/hicolor/scalable/apps/%{name}.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
mkdir -p %{buildroot}%{_datadir}/%{name}
cp -a usr/share/%{name}/icons %{buildroot}%{_datadir}/%{name}/
cp -a usr/share/%{name}/icons_dark %{buildroot}%{_datadir}/%{name}/
mkdir -p %{buildroot}%{_datadir}/locale
cp -a usr/share/locale/. %{buildroot}%{_datadir}/locale/
%find_lang %{name}

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop
python3 -m py_compile usr/lib/%{name}/%{name}.py \
    usr/lib/%{name}/yuki_iptv/*.py \
    usr/lib/%{name}/thirdparty/*.py

# Single package, no -lang subpackage: keeps things simple and avoids
# depending on %%lang_package behaving identically across distros. The
# translation files are still filtered correctly via %%find_lang, just
# folded into the main package via -f below.
%files -f %{name}.lang
%license COPYING LICENSE-CC-BY-4.0.txt LICENSE-NOTICE.txt
%doc README.md
%{_bindir}/%{name}
%{appdir}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_datadir}/%{name}/

%changelog
* Sat Aug 15 2026 itachi-re <https://github.com/itachi-re> - 260813.1-1
- Initial Fedora packaging
