#
# spec file for package yuki-iptv
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

%global appdir %{_prefix}/lib/%{name}

Name:           yuki-iptv
Version:        0
Release:        0
Summary:        IPTV player with EPG support
License:        GPL-3.0-or-later AND CC-BY-4.0
URL:            https://github.com/itachi-re/yuki-iptv
Source0:        %{name}-%{version}.tar.zst

BuildRequires:  desktop-file-utils
BuildRequires:  gettext-tools
BuildRequires:  hicolor-icon-theme
BuildRequires:  python3-base
BuildArch:      noarch

Requires:       ffmpeg
Requires:       hicolor-icon-theme
Requires:       libmpv2
Requires:       python3 >= 3.11
Requires:       python3-PyQt6
Requires:       python3-chardet
Requires:       python3-gobject
Requires:       python3-requests
Requires:       typelib-1_0-GLib-2_0
Requires:       typelib-1_0-Gio-2_0

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

%lang_package

%prep
%autosetup -p1

%build

make buildmo

# Bake the package version into the About dialog / --version output, mirroring
# what debian/rules does for __DEB_VERSION__ at install time.
sed -i 's/__DEB_VERSION__/%{version}/' usr/lib/%{name}/%{name}.py

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

%post
%desktop_database_post
%icon_theme_cache_post

%postun
%desktop_database_postun
%icon_theme_cache_postun

%files
%license COPYING LICENSE-CC-BY-4.0.txt LICENSE-NOTICE.txt
%doc README.md
%{_bindir}/%{name}
%{appdir}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_datadir}/%{name}/

%changelog
