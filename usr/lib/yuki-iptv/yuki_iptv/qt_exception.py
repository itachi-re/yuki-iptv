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
import sys
import logging
from PyQt6 import QtWidgets
from yuki_iptv.i18n import _

logger = logging.getLogger("yuki-iptv exception")


def show_exception(error, title=""):
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()  # noqa: F841
    if title:
        title = f"\n{title}"
    message = "{}{}\n\n{}".format(_("yuki-iptv error") + ":", title, str(error))
    logger.warning(message)
    msg = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Icon.Critical,
        _("Error"),
        message,
        QtWidgets.QMessageBox.StandardButton.Ok,
    )
    msg.exec()
