#
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
import logging
import traceback
import gi.repository.Gio

logger = logging.getLogger(__name__)


class Data:
    cookie = None
    session = None


def register():
    try:
        conn = gi.repository.Gio.bus_get_sync(gi.repository.Gio.BusType.SESSION, None)
    except Exception:
        logger.warning("D-Bus connection failed")
        logger.warning(traceback.format_exc())
        return
    try:
        Data.session = gi.repository.Gio.DBusProxy.new_sync(
            conn,
            0,
            None,
            "org.freedesktop.ScreenSaver",
            "/org/freedesktop/ScreenSaver",
            "org.freedesktop.ScreenSaver",
            None,
        )
    except Exception:
        logger.warning("org.freedesktop.ScreenSaver connection failed!")


def inhibit():
    if Data.session is not None and Data.cookie is None:
        try:
            Data.cookie = Data.session.Inhibit("(ss)", "yuki-iptv", "playing video")
            if not Data.cookie:
                raise Exception("cookie is None")
        except Exception:
            logger.warning("org.freedesktop.ScreenSaver.Inhibit failed")
            logger.warning(traceback.format_exc())


def uninhibit():
    if Data.session is not None and Data.cookie is not None:
        try:
            Data.session.UnInhibit("(u)", Data.cookie)
        except Exception:
            logger.warning("org.freedesktop.ScreenSaver.UnInhibit failed")
            logger.warning(traceback.format_exc())
        Data.cookie = None
