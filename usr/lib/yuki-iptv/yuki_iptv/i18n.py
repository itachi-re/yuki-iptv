#
# Copyright (c) 2021, 2022 Astroncia
# Copyright (c) 2023-2025 liya <liyaliya@tutamail.com>
#
# This file is part of yuki-iptv.
#
# yuki-iptv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# yuki-iptv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with yuki-iptv. If not, see <https://www.gnu.org/licenses/>.
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License.
# Font Awesome Free 5.15.4 by @fontawesome - https://fontawesome.com
# https://creativecommons.org/licenses/by/4.0/
#
import os
import locale
import os.path
import gettext
import logging
import traceback
from pathlib import Path
from PyQt6 import QtCore

logger = logging.getLogger(__name__)


class YukiLang:
    cache_gettext = {}
    cache_ngettext = {}


LOCALE_DIR = str(
    Path(
        Path(os.path.dirname(os.path.abspath(__file__))).parent.parent.parent,
        "share",
        "locale",
    )
)
locale.bindtextdomain("yuki-iptv", LOCALE_DIR)
gettext.bindtextdomain("yuki-iptv", LOCALE_DIR)
gettext.textdomain("yuki-iptv")


def cached_gettext(gettext_str):
    if gettext_str not in YukiLang.cache_gettext:
        YukiLang.cache_gettext[gettext_str] = gettext.gettext(gettext_str)
    return YukiLang.cache_gettext[gettext_str]


def cached_ngettext(*args):
    if args not in YukiLang.cache_ngettext:
        YukiLang.cache_ngettext[args] = gettext.ngettext(*args)
    return YukiLang.cache_ngettext[args]


_ = cached_gettext
ngettext = cached_ngettext


def load_qt_translations(app):
    try:
        translator = QtCore.QTranslator()
        if not translator.load(
            QtCore.QLocale.system(),
            "qtbase",
            "_",
            os.path.abspath(
                QtCore.QLibraryInfo.path(
                    QtCore.QLibraryInfo.LibraryPath.TranslationsPath
                )
            ),
            ".qm",
        ):
            logger.warning("System translations for Qt not loaded")
        app.installTranslator(translator)
    except Exception:
        logger.warning("Failed to set up system translations for Qt")
        logger.warning(traceback.format_exc())
