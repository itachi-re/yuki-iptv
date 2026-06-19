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
import base64
import hashlib
import logging
import traceback
from pathlib import Path
from yuki_iptv.args import loglevel
from yuki_iptv.xdg import CACHE_DIR
from yuki_iptv.requests_timeout import requests_get

logger = logging.getLogger(__name__)


def fetch_remote_channel_logo(channel_name, logo_url, ua, ref):
    logo_ret = None
    if not logo_url:
        return None
    cache_file = str(
        Path(
            CACHE_DIR,
            "logo",
            str(
                hashlib.sha512(
                    bytes(
                        base64.b64encode(bytes(logo_url, "utf-8")).decode("utf-8"),
                        "utf-8",
                    )
                ).hexdigest()
            )
            + ".img",
        )
    )
    if os.path.isfile(cache_file):
        # is remote logo, cache available
        logo_ret = cache_file
    else:
        try:
            if os.path.isfile(logo_url.strip()):
                # is local logo
                logo_ret = logo_url.strip()
            else:
                # is remote logo, cache is not available, fetching it
                req_headers = {"User-Agent": ua}
                if ref:
                    req_headers["Referer"] = ref
                req = requests_get(
                    logo_url,
                    headers=req_headers,
                    timeout=(3, 3),
                    stream=True,
                )
                if req.ok and req.content:
                    with open(cache_file, "wb") as im_file:
                        im_file.write(req.content)
                        logo_ret = cache_file
        except Exception:
            if loglevel.upper() == "DEBUG":
                logger.debug("Logging failed channel logo because loglevel is DEBUG")
                logger.debug(traceback.format_exc())
            logo_ret = None
    return logo_ret


def channel_logos_worker(requested_logos, update_dict, append=""):
    update_dict[f"logos{append}_inprogress"] = True
    for logo_channel in requested_logos:
        # logger.debug(f"Downloading logo for channel '{logo_channel}'...")
        logo_m3u = fetch_remote_channel_logo(
            logo_channel,
            requested_logos[logo_channel][0],
            requested_logos[logo_channel][2],
            requested_logos[logo_channel][3],
        )
        logo_epg = fetch_remote_channel_logo(
            logo_channel,
            requested_logos[logo_channel][1],
            requested_logos[logo_channel][2],
            requested_logos[logo_channel][3],
        )
        update_dict[f"LOGO{append}:::{logo_channel}"] = [logo_m3u, logo_epg]
    update_dict[f"logos{append}_inprogress"] = False
    update_dict[f"logos{append}_completed"] = True
