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
import logging
import datetime
from xml.etree.ElementTree import iterparse

logger = logging.getLogger(__name__)


def parse_timestamp(ts_string, settings):
    # Assume UTC if no timezone specified
    if " " not in ts_string.strip():
        ts_string += " +0000"

    ts = 0

    try:
        ts_string_split = ts_string.split(" ")

        tzinfo = ts_string_split[1]
        sign = 1
        if tzinfo.startswith("-"):
            sign = -1
        tzinfo = datetime.timezone(
            sign * datetime.timedelta(hours=int(tzinfo[1:3]), minutes=int(tzinfo[3:5]))
        )

        first = ts_string_split[0]

        try:
            ts = datetime.datetime(
                year=int(first[0:4]),
                month=int(first[4:6]),
                day=int(first[6:8]),
                hour=int(first[8:10]),
                minute=int(first[10:12]),
                second=int(first[12:14]),
                tzinfo=tzinfo,
            ).timestamp()
        except Exception:
            try:
                ts = datetime.datetime(
                    year=int(first[0:4]),
                    month=int(first[4:6]),
                    day=int(first[6:8]),
                    hour=int(first[8:10]),
                    minute=int(first[10:12]),
                    tzinfo=tzinfo,
                ).timestamp()
            except Exception:
                try:
                    ts = datetime.datetime(
                        year=int(first[0:4]),
                        month=int(first[4:6]),
                        day=int(first[6:8]),
                        hour=int(first[8:10]),
                        tzinfo=tzinfo,
                    ).timestamp()
                except Exception:
                    try:
                        ts = datetime.datetime(
                            year=int(first[0:4]),
                            month=int(first[4:6]),
                            day=int(first[6:8]),
                            tzinfo=tzinfo,
                        ).timestamp()
                    except Exception:
                        try:
                            ts = datetime.datetime(
                                year=int(first[0:4]),
                                month=int(first[4:6]),
                                day=1,
                                tzinfo=tzinfo,
                            ).timestamp()
                        except Exception:
                            try:
                                ts = datetime.datetime(
                                    year=int(first[0:4]), month=1, day=1, tzinfo=tzinfo
                                ).timestamp()
                            except Exception:
                                pass

        if ts != 0:
            ts += 3600 * settings["epgoffset"]
    except Exception:
        pass

    return ts


def parse_as_xmltv(data, settings):
    icon = ""
    title = ""
    desc = ""
    category = ""

    ret = {
        "display_names": [],
        "ids": {},
        "names": {},
        "_names": set(),
        "icons": {},
        "epg": {},
    }

    for event, elem in iterparse(data):
        if event == "end":
            if elem.tag == "display-name":
                if elem.text:
                    ret["display_names"].append(elem.text)
            elif elem.tag == "icon":
                if "src" in elem.attrib:
                    icon = elem.attrib["src"]
            elif elem.tag == "channel":
                if "id" in elem.attrib:
                    id = elem.attrib["id"]
                    if id not in ret["ids"]:
                        ret["ids"][id] = set()
                    first = True
                    for display_name in ret["display_names"]:
                        ret["ids"][id].add(display_name)
                        ret["names"][display_name.lower().strip()] = id
                        if first:
                            first = False
                            ret["_names"].add(display_name.strip())
                    ret["icons"][id] = icon
                    ret["display_names"].clear()
                    icon = ""
            elif elem.tag == "title":
                if elem.text:
                    title = elem.text
            elif elem.tag == "desc":
                if elem.text:
                    desc = elem.text
            elif elem.tag == "category":
                if elem.text:
                    category = elem.text
            elif elem.tag == "programme":
                if (
                    "start" in elem.attrib
                    and "stop" in elem.attrib
                    and "channel" in elem.attrib
                    and elem.attrib["start"]
                    and elem.attrib["stop"]
                    and elem.attrib["channel"]
                ):
                    catchup_id = ""
                    if "catchup-id" in elem.attrib and elem.attrib["catchup-id"]:
                        catchup_id = elem.attrib["catchup-id"]
                    if elem.attrib["channel"] not in ret["epg"]:
                        ret["epg"][elem.attrib["channel"]] = []
                    start = parse_timestamp(elem.attrib["start"], settings)
                    stop = parse_timestamp(elem.attrib["stop"], settings)
                    e = {
                        "start": start,
                        "stop": stop,
                        "title": title,
                        "desc": desc,
                        "category": category,
                        "catchup-id": catchup_id,
                    }
                    ret["epg"][elem.attrib["channel"]].append(e)
                title = ""
                desc = ""
                category = ""
            elem.clear()
    return ret
