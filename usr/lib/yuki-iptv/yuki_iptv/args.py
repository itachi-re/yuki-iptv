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
import argparse

parser = argparse.ArgumentParser(
    prog="yuki-iptv", description="IPTV player with EPG support"
)
parser.add_argument("--version", action="store_true", help="Show version")
parser.add_argument(
    "--loglevel",
    action="store",
    help="Log level (CRITICAL, ERROR, WARNING, INFO, DEBUG) default: INFO",
)
parsed_args, _unparsed_args = parser.parse_known_args()

loglevel = parsed_args.loglevel if parsed_args.loglevel else "INFO"
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError("Invalid log level: %s" % loglevel)

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(name)s %(levelname)s: %(message)s",
    level=numeric_level,
    datefmt="%H:%M:%S",
)
