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
import hashlib
import logging
import traceback
from PyQt6 import QtWidgets
from functools import partial
from yuki_iptv.i18n import _
from yuki_iptv.misc import YukiData
from yuki_iptv.threads import execute_in_main_thread
from thirdparty.xtream import XTream

logger = logging.getLogger(__name__)


class XTreamFailedClass:
    auth_data = {}


def log_xtream(*args):
    logger.info(" ".join([str(arg) for arg in args]))


def xtream_init_failure(exc):
    msg3 = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Icon.Warning,
        _("Error"),
        exc,
        QtWidgets.QMessageBox.StandardButton.Ok,
    )
    msg3.exec()


def load_xtream(xtream_url, headers=None):
    (
        _xtream_unused,
        xtream_username,
        xtream_password,
        xtream_url,
    ) = xtream_url.split("::::::::::::::")
    xtream_headers = {
        "User-Agent": (
            YukiData.settings["playlist_useragent"]
            if YukiData.settings["playlist_useragent"]
            else YukiData.settings["ua"]
        )
    }
    referer = (
        YukiData.settings["playlist_referer"]
        if YukiData.settings["playlist_referer"]
        else YukiData.settings["referer"]
    )
    if referer:
        xtream_headers["Referer"] = referer
    if headers:
        if "Referer" in headers and not headers["Referer"]:
            headers.pop("Referer")
        xtream_headers = headers
    logger.info(f"Loading XTream with headers {json.dumps(xtream_headers)}")
    try:
        xt = XTream(
            log_xtream,
            hashlib.sha512(YukiData.settings["m3u"].encode("utf-8")).hexdigest(),
            xtream_username,
            xtream_password,
            xtream_url,
            headers=xtream_headers,
            hide_adult_content=False,
            cache_path="",
        )
    except Exception:
        exc = traceback.format_exc()
        logger.warning("XTream init failure")
        logger.warning(exc)
        execute_in_main_thread(partial(xtream_init_failure, exc))
        xt = XTreamFailedClass()
    return xt, xtream_username, xtream_password, xtream_url


def convert_xtream_to_m3u(data, skip_init=False, append_group=""):
    output = "#EXTM3U\n" if not skip_init else ""

    for channel in data:
        name = channel.name
        epg_channel_id = channel.epg_channel_id if channel.epg_channel_id else ""
        group = channel.group_title if channel.group_title else ""
        if append_group:
            group = append_group + " " + group
        logo = channel.logo if channel.logo else ""
        url = channel.url

        line = "#EXTINF:0"
        if epg_channel_id:
            line += f' tvg-id="{epg_channel_id}"'
        if logo:
            line += f' tvg-logo="{logo}"'
        if group:
            line += f' group-title="{group}"'
        line += f",{name}"

        output += line + "\n" + url + "\n"

    return output
