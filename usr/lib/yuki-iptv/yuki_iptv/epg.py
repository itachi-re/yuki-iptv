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
import io
import os
import os.path
import time
import gzip
import lzma
import json
import logging
import hashlib
import zipfile
import datetime
import traceback
from pathlib import Path
from yuki_iptv.i18n import _
from yuki_iptv.xdg import CACHE_DIR
from yuki_iptv.epg_xmltv import parse_as_xmltv
from yuki_iptv.epg_jtv import parse_epg_zip_jtv
from yuki_iptv.requests_timeout import requests_get

logger = logging.getLogger(__name__)
epg_array = {}


def load_epg(epg_url, headers):
    logger.info("Loading EPG...")
    # logger.debug(f"Address: '{epg_url}'")
    if os.path.isfile(epg_url.strip()):
        epg_file = open(epg_url.strip(), "rb")
        epg = epg_file.read()
        epg_file.close()
    else:
        logger.info(f"Headers: {json.dumps(headers)}")
        epg_req = requests_get(epg_url, headers=headers, stream=True, timeout=(35, 35))
        logger.info(f"EPG URL status code: {epg_req.status_code}")
        epg = epg_req.content
    logger.info("EPG loaded")
    return epg


def is_program_actual(sets0, future=False):
    if future:
        current_time = time.time() + 86400  # 1 day
    else:
        current_time = time.time()
    if sets0:
        for prog1 in sets0:
            pr1 = sets0[prog1]
            for p in pr1:
                if current_time > p["start"] and current_time < p["stop"]:
                    return True
    return False


def parse_epg(epg_url, settings, return_dict, i, epgs):
    epg_failed = False
    epg_outdated = False
    epg_cache_filename_hash = hashlib.sha512(epg_url.encode("utf-8")).hexdigest()
    epg_cache_filename = Path(CACHE_DIR, "epg", epg_cache_filename_hash + ".dat")
    epg_date_filename = Path(CACHE_DIR, "epg", epg_cache_filename_hash + ".txt")
    cache_used = False
    if (
        os.path.isfile(epg_cache_filename)
        and os.path.isfile(epg_date_filename)
        and not settings["nocacheepg"]
    ):
        with open(epg_date_filename, "r") as epg_date_file:
            epg_date = int(float(epg_date_file.read().strip()))
            time_diff = int(time.time() - epg_date)
            logger.debug(f"EPG last updated {time_diff} seconds ago")
            if time_diff < 86400:  # 1 day
                with open(epg_cache_filename, "rb") as epg_cache_file:
                    logger.info("Reading cached EPG...")
                    epg_data = epg_cache_file.read()
                    cache_used = True
            else:
                logger.info("Cache is older than 1 day, removing")
    if not cache_used:
        user_agent = (
            settings["playlist_useragent"]
            if settings["playlist_useragent"]
            else settings["ua"]
        )
        referer = (
            settings["playlist_referer"]
            if settings["playlist_referer"]
            else settings["referer"]
        )
        headers = {"User-Agent": user_agent}
        if referer:
            headers["Referer"] = referer
        originURL = ""
        if referer and referer.endswith("/"):
            originURL = referer[:-1]
        if originURL:
            headers["Origin"] = originURL
        epg_data = load_epg(epg_url, headers)

    return_dict["epg_progress"] = _("Updating TV guide... (parsing {}/{})").format(
        i, len(epgs)
    )

    obj = io.BytesIO(epg_data)
    if zipfile.is_zipfile(obj):
        logger.info("ZIP file detected")
        found_zip_format = False
        with zipfile.ZipFile(obj) as myzip:
            namelist = myzip.namelist()
            for name in namelist:
                if name.endswith(".xml"):
                    logger.info("XMLTV inside ZIP detected, trying to parse...")
                    found_zip_format = True
                    with myzip.open(name) as myfile:
                        try:
                            epg = parse_as_xmltv(myfile, settings)
                        except Exception:
                            logger.info("Failed to parse as XMLTV!")
                            epg = {"epg": None}
                    break
                if name.endswith(".ndx"):
                    logger.info("JTV format detected, trying to parse...")
                    found_zip_format = True
                    epg = parse_epg_zip_jtv(myzip)
                    break
        if not found_zip_format:
            logger.warning("No known EPG formats found in ZIP file!")
            epg = {"epg": None}
    else:
        try:
            logger.info("Trying XMLTV gzip...")
            data = gzip.GzipFile(fileobj=io.BytesIO(epg_data))
            epg = parse_as_xmltv(data, settings)
        except Exception:
            logger.info("Trying XMLTV lzma...")
            try:
                data = lzma.LZMAFile(filename=io.BytesIO(epg_data))
                epg = parse_as_xmltv(data, settings)
            except Exception:
                logger.info("Trying XMLTV raw...")
                try:
                    epg = parse_as_xmltv(io.BytesIO(epg_data), settings)
                except Exception:
                    logger.info("Unknown EPG format!")
                    epg = {"epg": None}
    if not epg["epg"]:
        epg_failed = True
    else:
        if is_program_actual(epg["epg"], future=cache_used):
            if epg_url in epg_array:
                epg_array.pop(epg_url)
            epg_array[epg_url] = epg
            epg = None
        else:
            logger.warning("Programme not actual")
            epg_outdated = True
    if epg_data and not epg_failed and not epg_outdated:
        if not cache_used and not settings["nocacheepg"]:
            logger.info("Saving EPG cache...")
            with open(epg_cache_filename, "wb") as epg_cache_file:
                epg_cache_file.write(epg_data)
            with open(epg_date_filename, "w") as epg_date_file:
                epg_date_file.write(f"{int(time.time())}\n")
    else:
        if os.path.isfile(epg_cache_filename):
            os.remove(epg_cache_filename)
        if os.path.isfile(epg_date_filename):
            os.remove(epg_date_filename)
    return epg_failed, epg_outdated, cache_used


def epg_worker(epg_settings_url, settings, return_dict):
    epg_failed = False
    epg_outdated = False
    try:
        # Some playlists use comma as EPG urls separator, some - semicolon
        epgs = [
            epg_url.strip() for epg_url in epg_settings_url.replace(";", ",").split(",")
        ]
        if epgs:
            t = time.time()
            logger.info("Updating EPG...")
            i = 0
            for epg_url in epgs:
                try:
                    i += 1

                    return_dict["epg_progress"] = _(
                        "Updating TV guide... (loading {}/{})"
                    ).format(i, len(epgs))

                    epg_failed_, epg_outdated_, cache_used = parse_epg(
                        epg_url, settings, return_dict, i, epgs
                    )
                    if cache_used and (epg_failed_ or epg_outdated_):
                        logger.info("Trying without cache...")
                        epg_failed_, epg_outdated_, cache_used = parse_epg(
                            epg_url, settings, return_dict, i, epgs
                        )
                    if epg_failed_:
                        epg_failed = epg_failed_
                    if epg_outdated_:
                        epg_outdated = epg_outdated_
                except Exception:
                    epg_failed = True
                    logger.warning(traceback.format_exc())
            logger.info(f"Updating EPG done, took {round(time.time() - t, 2)} seconds")
    except Exception:
        epg_failed = True
        logger.warning(traceback.format_exc())
    return epg_failed, epg_outdated, epg_array


def worker_get_epg_id(tvg_id, tvg_name, channel_name, epg_name, epg_array):
    epg_name = epg_name.lower().strip()
    channel_name = channel_name.lower().strip()
    tvg_name = tvg_name.lower().strip()
    found_id = ""
    for data in epg_array:
        # First, match from EPG name
        if epg_name and epg_name in epg_array[data]["names"]:
            found_id = epg_array[data]["names"][epg_name]
            break
        elif epg_name and epg_name.replace(" ", "_") in epg_array[data]["names"]:
            found_id = epg_array[data]["names"][epg_name.replace(" ", "_")]
            break
        # Second, match from tvg-id
        elif tvg_id and tvg_id in epg_array[data]["ids"]:
            found_id = tvg_id
            break
        # Third, match from tvg-name
        elif tvg_name and tvg_name in epg_array[data]["names"]:
            found_id = epg_array[data]["names"][tvg_name]
            break
        elif tvg_name and tvg_name.replace(" ", "_") in epg_array[data]["names"]:
            found_id = epg_array[data]["names"][tvg_name.replace(" ", "_")]
            break
        # Last, match from channel name
        elif channel_name and channel_name in epg_array[data]["names"]:
            found_id = epg_array[data]["names"][channel_name]
            break
        elif (
            channel_name and channel_name.replace(" ", "_") in epg_array[data]["names"]
        ):
            found_id = epg_array[data]["names"][channel_name.replace(" ", "_")]
            break
    if not found_id:
        found_id = ""
    return found_id


def worker_get_epg_programmes(epg_id, epg_array):
    ret = None
    for data in epg_array:
        if epg_id and epg_id in epg_array[data]["epg"]:
            ret = epg_array[data]["epg"][epg_id]
            break
    if ret:
        # Sort EPG entries by start time
        ret.sort(key=lambda programme: programme["start"])
    return ret


def worker_get_current_programme(epg_id, epg_array):
    ret = None
    if epg_id:
        programmes = worker_get_epg_programmes(epg_id, epg_array)
        if programmes:
            for prog in programmes:
                if time.time() > prog["start"] and time.time() < prog["stop"]:
                    ret = prog
                    break
    return ret


def worker_get_epg_icon(epg_id, epg_array):
    ret = ""
    for data in epg_array:
        if epg_id and epg_id in epg_array[data]["icons"]:
            ret = epg_array[data]["icons"][epg_id]
            break
    if not ret:
        ret = ""
    return ret


def worker_check_programmes_actual(epg_array):
    program_actual = True
    for data in epg_array:
        if not is_program_actual(epg_array[data]["epg"]):
            program_actual = False
            break
    return program_actual


def worker_get_all_epg_names(epg_array):
    names = set()
    for data in epg_array:
        d = epg_array[data]
        if "_names" in d:
            names_epg = d["_names"]
        else:
            names_epg = d["names"]
        if names_epg:
            for name in names_epg:
                names.add(name)
    return names


def epg_is_in_date(programme, date_selected):
    day_start_ts = int(date_selected.timestamp())
    day_end_ts = int(
        datetime.datetime(
            date_selected.year, date_selected.month, date_selected.day, 23, 59, 59
        ).timestamp()
    )
    return programme["start"] < day_end_ts and programme["stop"] > day_start_ts
