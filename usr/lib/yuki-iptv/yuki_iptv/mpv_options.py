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
import json
import shlex
import logging
import traceback
from PyQt6 import QtWidgets
from yuki_iptv.i18n import _
from thirdparty import mpv

logger = logging.getLogger(__name__)


def show_parse_error(options):
    msg_wrongmpvoptions = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Icon.Warning,
        "yuki-iptv",
        _("Custom MPV options invalid, ignoring them") + f"\n\n{options}",
        QtWidgets.QMessageBox.StandardButton.Ok,
    )
    msg_wrongmpvoptions.exec()


def get_mpv_options(options, custom_options):
    options_orig = options.copy()
    options_custom_array = {}
    try:
        pairs = shlex.split(custom_options)
        keys = {}
        for pair in pairs:
            key, value = pair.split("=", 1)
            if key.startswith("--"):
                key = key.replace("--", "")
            if key.endswith("-append"):
                key = key.replace("-append", "")
                if key not in keys:
                    keys[key] = ""
                v = value.replace("=", '="', 1)
                keys[key] = f'{keys[key]},{v}"'.lstrip(",")
            else:
                keys[key] = value
        for key in keys:
            options[key] = keys[key]
            options_custom_array[key] = keys[key]
    except Exception:
        logger.warning("Could not parse mpv options!")
        logger.warning(traceback.format_exc())
        show_parse_error(custom_options)
    logger.info("Testing custom mpv options...")
    logger.info(options_custom_array)
    try:
        mpv.MPV(**options_custom_array)
        logger.info("mpv options OK")
    except Exception:
        logger.warning("mpv options test failed, ignoring them")
        show_parse_error(json.dumps(options_custom_array))
        options = options_orig
    return options, options_custom_array
