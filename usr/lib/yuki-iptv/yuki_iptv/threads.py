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
import traceback
from PyQt6 import QtCore
from functools import partial

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    execute_in_main_thread = QtCore.pyqtSignal(partial)


comm_instance = Communicate()
comm_instance.execute_in_main_thread.connect(lambda function: function())


def execute_in_main_thread(fn):
    try:
        comm_instance.execute_in_main_thread.emit(fn)
    except Exception as exc:
        if not isinstance(exc, RuntimeError):
            logger.warning("execute_in_main_thread failed")
            logger.warning(traceback.format_exc())
