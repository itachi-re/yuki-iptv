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
import os.path
import json
import logging
import datetime
import traceback
import threading
from pathlib import Path
from functools import partial
from PyQt6 import QtCore, QtGui, QtWidgets
from yuki_iptv.i18n import _, ngettext
from yuki_iptv.xdg import LOCAL_DIR
from yuki_iptv.misc import YukiData
from yuki_iptv.xtream import load_xtream
from yuki_iptv.qt_exception import show_exception
from yuki_iptv.gui import move_window_to_center
from yuki_iptv.threads import execute_in_main_thread

logger = logging.getLogger(__name__)

all_files_lang = _("All Files")


class Data:
    playlists_win = None
    windows = []


class PlaylistsWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.name_label = QtWidgets.QLabel()
        self.name_label.setFont(YukiData.YukiGUI.font_bold)
        self.description_label = QtWidgets.QLabel()
        self.description_label.setFont(YukiData.YukiGUI.font_italic)
        self.description_label.setWordWrap(True)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setPixmap(YukiData.YukiGUI.tv_icon)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.description_label)
        self.layout.setSpacing(0)

        self.layout2 = QtWidgets.QGridLayout()
        self.layout2.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.layout2.addWidget(self.icon_label, 0, 0)
        self.layout2.addLayout(self.layout, 0, 1)
        self.layout2.setSpacing(10)

        self.wg = QtWidgets.QWidget()
        self.wg.setLayout(self.layout2)

        self.btn_select = QtWidgets.QPushButton()
        self.btn_select.setToolTip(_("Select"))
        self.btn_select.setIcon(
            QtGui.QIcon(str(Path(YukiData.YukiGUI.icons_folder, "select.png")))
        )
        self.btn_select.setMaximumWidth(32)

        self.btn_edit = QtWidgets.QPushButton()
        self.btn_edit.setToolTip(_("Edit"))
        self.btn_edit.setIcon(
            QtGui.QIcon(str(Path(YukiData.YukiGUI.icons_folder, "edit_playlist.png")))
        )
        self.btn_edit.setMaximumWidth(32)

        self.btn_delete = QtWidgets.QPushButton()
        self.btn_delete.setToolTip(_("Delete"))
        self.btn_delete.setIcon(
            QtGui.QIcon(str(Path(YukiData.YukiGUI.icons_folder, "trash.png")))
        )
        self.btn_delete.setMaximumWidth(32)

        self.wg2 = QtWidgets.QWidget()
        self.la2 = QtWidgets.QHBoxLayout()
        self.la2.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.la2.addWidget(self.btn_select)
        self.la2.addWidget(self.btn_edit)
        self.la2.addWidget(self.btn_delete)
        self.wg2.setLayout(self.la2)

        self.layout3 = QtWidgets.QHBoxLayout()
        self.layout3.setSpacing(0)
        self.layout3.setContentsMargins(0, 0, 0, 0)
        self.layout3.addWidget(self.wg)
        self.layout3.addWidget(self.wg2)

        self.setLayout(self.layout3)


class PlaylistsWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(500, 600)
        self.setWindowTitle(_("Playlists"))
        self.setWindowIcon(YukiData.YukiGUI.main_icon)

        self.yuki_iptv_icon = QtWidgets.QLabel()
        self.yuki_iptv_icon.setPixmap(YukiData.YukiGUI.tv_icon)

        self.yuki_iptv_label = QtWidgets.QLabel()
        self.yuki_iptv_label.setFont(YukiData.YukiGUI.font_11_bold)
        self.yuki_iptv_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        yuki_color = "#1b1c1c;"
        if YukiData.use_dark_icon_theme:
            yuki_color = "white"
        self.yuki_iptv_label.setText(
            f'&nbsp;<span style="color: {yuki_color};">yuki-iptv</span>'
        )

        self.yuki_iptv = QtWidgets.QWidget()
        self.yuki_iptv_layout = QtWidgets.QHBoxLayout()
        self.yuki_iptv_layout.addWidget(self.yuki_iptv_icon)
        self.yuki_iptv_layout.addWidget(self.yuki_iptv_label)
        self.yuki_iptv.setLayout(self.yuki_iptv_layout)

        self.playlists_add = QtWidgets.QPushButton()
        self.playlists_add.setToolTip(_("Add playlist"))
        self.playlists_add.setIcon(
            QtGui.QIcon(str(Path(YukiData.YukiGUI.icons_folder, "add.png")))
        )
        self.playlists_add.clicked.connect(add_playlist)

        # self.playlists_favourites_plus = QtWidgets.QPushButton()
        # self.playlists_favourites_plus.setToolTip(_("Favourites+"))
        # self.playlists_favourites_plus.setIcon(
        #     QtGui.QIcon(str(Path(YukiData.YukiGUI.icons_folder, "star.png")))
        # )
        self.playlists_settings = QtWidgets.QPushButton()
        self.playlists_settings.setToolTip(_("Settings"))
        self.playlists_settings.setIcon(
            QtGui.QIcon(str(Path(YukiData.YukiGUI.icons_folder, "settings.png")))
        )
        self.playlists_settings.clicked.connect(lambda: YukiData.show_settings())

        self.buttons = QtWidgets.QWidget()
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.addWidget(self.playlists_add)
        # self.buttons_layout.addWidget(self.playlists_favourites_plus)
        self.buttons_layout.addWidget(self.playlists_settings)
        self.buttons.setLayout(self.buttons_layout)

        self.empty_label = QtWidgets.QLabel()

        self.playlists_widget = QtWidgets.QWidget()
        self.playlists_layout = QtWidgets.QHBoxLayout()
        self.playlists_layout.addWidget(self.empty_label)
        self.playlists_layout.setAlignment(
            self.empty_label, QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        self.playlists_layout.addWidget(self.yuki_iptv)
        self.playlists_layout.setAlignment(
            self.yuki_iptv, QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        self.playlists_layout.addWidget(self.buttons)
        self.playlists_layout.setAlignment(
            self.buttons, QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.playlists_widget.setLayout(self.playlists_layout)

        self.playlists_layout.setContentsMargins(0, 0, 0, 0)

        self.search_icon = QtWidgets.QLabel()
        self.search_icon.setPixmap(YukiData.YukiGUI.search_icon_pixmap_small)

        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText(_("Search playlists by title"))
        self.search_edit.textChanged.connect(do_search)

        self.search_widget = QtWidgets.QWidget()
        self.search_layout = QtWidgets.QHBoxLayout()
        self.search_layout.addWidget(self.search_icon)
        self.search_layout.addWidget(self.search_edit)
        self.search_widget.setLayout(self.search_layout)

        self.playlists_list = QtWidgets.QListWidget()
        self.playlists_list.itemDoubleClicked.connect(playlist_selected)

        self.playlists_notice_label = QtWidgets.QLabel(
            _("Please select a playlist from the list or add a new playlist")
        )
        yuki_color_2 = "#424242"
        if YukiData.use_dark_icon_theme:
            yuki_color_2 = "white"
        self.playlists_notice_label.setStyleSheet(
            f"color: {yuki_color_2}; font-size: 0.7em;"
        )

        self.playlists_notice = QtWidgets.QWidget()
        self.playlists_notice_layout = QtWidgets.QHBoxLayout()
        self.playlists_notice_layout.addWidget(self.playlists_notice_label)
        self.playlists_notice_layout.setContentsMargins(0, 0, 0, 0)
        self.playlists_notice_layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.playlists_notice.setLayout(self.playlists_notice_layout)

        self.playlists_win_widget_main = QtWidgets.QWidget()
        self.playlists_win_widget_main_layout = QtWidgets.QVBoxLayout()
        self.playlists_win_widget_main_layout.addWidget(self.playlists_widget)
        self.playlists_win_widget_main_layout.addWidget(self.playlists_notice)
        self.playlists_win_widget_main_layout.addWidget(self.search_widget)
        self.playlists_win_widget_main_layout.addWidget(self.playlists_list)
        self.playlists_win_widget_main.setLayout(self.playlists_win_widget_main_layout)

        self.setCentralWidget(self.playlists_win_widget_main)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent):
        mime_data = event.mimeData()
        file_urls = mime_data.urls()

        for url in file_urls:
            file_path = url.toLocalFile()
            if True:  # os.path.isfile(file_path):
                name = os.path.basename(file_path)
                playlist = {
                    "m3u": file_path,
                    "epg": "",
                    "epgoffset": 0,
                    "added": datetime.datetime.now().timestamp(),
                }
                if name in YukiData.playlists_saved:
                    name = f"{name} "
                YukiData.playlists_saved[name] = playlist

        save_playlists()
        populate_playlists()


def do_search():
    YukiData.playlists_search = Data.playlists_win.search_edit.text()
    populate_playlists()


def add_playlist():
    win = Playlists_Edit()
    Data.windows.append(win)
    win.show()


def create_playlists_window():
    Data.playlists_win = PlaylistsWindow()
    Data.playlists_shortcut_search_ctrl = QtGui.QShortcut(
        QtGui.QKeySequence(QtCore.Qt.Modifier.CTRL | QtCore.Qt.Key.Key_F),
        Data.playlists_win,
        activated=Data.playlists_win.search_edit.setFocus,
    )
    Data.playlists_shortcut_search_meta = QtGui.QShortcut(
        QtGui.QKeySequence(QtCore.Qt.Modifier.META | QtCore.Qt.Key.Key_F),
        Data.playlists_win,
        activated=Data.playlists_win.search_edit.setFocus,
    )


def favourites_plus():
    Data.playlists_win.close()
    YukiData.YukiGUI.m3u = str(Path(LOCAL_DIR, "favplaylist.m3u"))
    YukiData.YukiGUI.epg = ""
    YukiData.YukiGUI.soffset.setValue(0)
    YukiData.save_settings()


class Playlists_Edit(QtWidgets.QMainWindow):
    def __init__(self, overwrite=False, overwrite_name=""):
        super().__init__()
        self.resize(500, 180)
        self.setWindowTitle(_("Playlists"))
        self.setWindowIcon(YukiData.YukiGUI.main_icon)

        self.name_label = QtWidgets.QLabel("{}:".format(_("Name")))
        self.path_label = QtWidgets.QLabel("{}:".format(_("M3U / XSPF playlist")))
        self.epg_label = QtWidgets.QLabel("{}:".format(_("TV guide\naddress")))
        self.name_edit = QtWidgets.QLineEdit()

        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setPlaceholderText(_("Path to file or URL"))

        self.path_file = QtWidgets.QPushButton()
        self.path_file.setIcon(
            QtGui.QIcon(str(Path(YukiData.YukiGUI.icons_folder, "file.png")))
        )

        def path_file_clicked():
            path_filename = QtWidgets.QFileDialog.getOpenFileName(
                self,
                _("Select playlist"),
                str(Path.home()),
                f"{all_files_lang} (*);;M3U (*.m3u *.m3u8);;XSPF (*.xspf)",
            )[0]
            if path_filename:
                self.path_edit.setText(path_filename)

        self.path_file.clicked.connect(path_file_clicked)

        def epg_file_clicked(_epg_edit):
            epg_filename = QtWidgets.QFileDialog.getOpenFileName(
                self,
                _("Select EPG file"),
                str(Path.home()),
                f"{all_files_lang} (*);;XMLTV (*.xml *.xml.gz *.xml.xz);;JTV (*.zip)",
            )[0]
            if epg_filename:
                _epg_edit.setText(epg_filename)

        self.epg_edits = []

        def _epg_edits_add():
            epg_edits_add()
            redraw_layout()

        def epg_edits_remove(val):
            self.epg_edits.remove(val)
            redraw_layout()

        def epg_edits_add():
            epg_edit = QtWidgets.QLineEdit()
            epg_edit.setPlaceholderText(_("Path to file or URL"))

            epg_file = QtWidgets.QPushButton()
            epg_file.setIcon(
                QtGui.QIcon(str(Path(YukiData.YukiGUI.icons_folder, "file.png")))
            )
            epg_file.clicked.connect(partial(epg_file_clicked, epg_edit))

            epg_add = QtWidgets.QPushButton()
            epg_add.setIcon(YukiData.YukiGUI.plus_icon)
            epg_add.setToolTip(_("Add"))
            epg_add.clicked.connect(_epg_edits_add)

            epg_remove = QtWidgets.QPushButton()
            epg_remove.setIcon(YukiData.YukiGUI.minus_icon)
            epg_remove.setToolTip(_("Remove"))

            if self.epg_edits:
                val = [epg_edit, epg_file, epg_add, epg_remove]
            else:
                val = [epg_edit, epg_file, epg_add]

            self.epg_edits.append(val)

            epg_remove.clicked.connect(partial(epg_edits_remove, val))

        epg_edits_add()

        self.useragent_label = QtWidgets.QLabel("{}:".format(_("User agent")))
        self.useragent_edit = QtWidgets.QLineEdit()
        self.useragent_edit.setPlaceholderText(YukiData.settings["ua"])

        self.referer_label = QtWidgets.QLabel(_("HTTP Referer:"))
        self.referer_edit = QtWidgets.QLineEdit()
        self.referer_edit.setPlaceholderText(YukiData.settings["referer"])

        self.playlist_type = "local"

        def set_xtream():
            self.playlist_type = "xtream"
            redraw_layout()

        self.btn_xtream = QtWidgets.QPushButton("XTream")
        self.btn_xtream.clicked.connect(set_xtream)
        self.xtream_username_label = QtWidgets.QLabel("{}:".format(_("Username")))
        self.xtream_username = QtWidgets.QLineEdit()
        self.xtream_password_label = QtWidgets.QLabel("{}:".format(_("Password")))
        self.xtream_password = QtWidgets.QLineEdit()
        self.xtream_url_label = QtWidgets.QLabel("{}:".format(_("URL")))
        self.xtream_url = QtWidgets.QLineEdit()

        self.save_btn = QtWidgets.QPushButton(_("Save"))
        self.save_btn.setFont(YukiData.YukiGUI.font_bold)
        self.save_btn.clicked.connect(partial(self.on_save, overwrite))

        self.epg_offset_edit = QtWidgets.QDoubleSpinBox()
        self.epg_offset_edit.setMinimum(-240)
        self.epg_offset_edit.setMaximum(240)
        self.epg_offset_edit.setSingleStep(1)
        self.epg_offset_edit.setDecimals(1)

        self.udp_proxy_label = QtWidgets.QLabel(_("UDP proxy") + ":")
        self.udp_proxy_edit = QtWidgets.QLineEdit()
        self.udp_proxy_edit.setPlaceholderText(YukiData.settings["udp_proxy"])

        self.old_name = ""

        if overwrite and overwrite_name:
            overwrite_path = overwrite["m3u"]
            overwrite_epg = ""
            overwrite_useragent = ""
            overwrite_referer = ""
            overwrite_udp_proxy = ""
            if "epg" in overwrite and overwrite["epg"]:
                overwrite_epg = overwrite["epg"]
            overwrite_epg_offset = 0
            if "epgoffset" in overwrite and overwrite["epgoffset"]:
                overwrite_epg_offset = overwrite["epgoffset"]
            if "useragent" in overwrite and overwrite["useragent"]:
                overwrite_useragent = overwrite["useragent"]
            if "udp_proxy" in overwrite and overwrite["udp_proxy"]:
                overwrite_udp_proxy = overwrite["udp_proxy"]
            if "referer" in overwrite and overwrite["referer"]:
                overwrite_referer = overwrite["referer"]

            self.name_edit.setText(overwrite_name)
            self.useragent_edit.setText(overwrite_useragent)
            self.referer_edit.setText(overwrite_referer)
            self.udp_proxy_edit.setText(overwrite_udp_proxy)
            self.old_name = overwrite_name
            if overwrite_path.startswith("XTREAM::::::::::::::"):
                self.playlist_type = "xtream"
                xtream = overwrite_path.split("::::::::::::::")
                self.xtream_username.setText(xtream[1])
                self.xtream_password.setText(xtream[2])
                self.xtream_url.setText(xtream[3])
            else:
                self.path_edit.setText(overwrite_path)
            first = True
            for epg_path in overwrite_epg.split(","):
                if first:
                    first = False
                    continue
                epg_edits_add()
            _i = -1
            for epg_path in overwrite_epg.split(","):
                _i += 1
                self.epg_edits[_i][0].setText(epg_path)
            self.epg_offset_edit.setValue(overwrite_epg_offset)

        self.offset_label = QtWidgets.QLabel("{}:".format(_("TV guide offset")))
        self.offset_label_hours = QtWidgets.QLabel(
            (ngettext("%d hour", "%d hours", 0) % 0).replace("0 ", "")
        )

        self.more_settings_shown = False

        def more_settings_clicked():
            self.more_settings_shown = not self.more_settings_shown
            if self.more_settings_shown:
                self.more_settings.setIcon(YukiData.YukiGUI.minus_icon)
            else:
                self.more_settings.setIcon(YukiData.YukiGUI.plus_icon)
            redraw_layout()

        self.more_settings = QtWidgets.QPushButton(_("Settings"))
        self.more_settings.setIcon(YukiData.YukiGUI.plus_icon)
        self.more_settings.clicked.connect(more_settings_clicked)

        self.widget = QtWidgets.QWidget()

        self.layout = QtWidgets.QGridLayout()
        self.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )

        def redraw_layout():
            for _i in reversed(range(self.layout.count())):
                self.layout.itemAt(_i).widget().setParent(None)
            self.layout.addWidget(self.name_label, 0, 0)
            self.layout.addWidget(self.name_edit, 0, 1)
            if self.playlist_type == "local":
                self.layout.addWidget(self.path_label, 1, 0)
                self.layout.addWidget(self.path_edit, 1, 1)
                self.layout.addWidget(self.path_file, 1, 2)
                self.layout.addWidget(self.btn_xtream, 2, 0)
                i = 2
            elif self.playlist_type == "xtream":
                self.layout.addWidget(self.xtream_username_label, 1, 0)
                self.layout.addWidget(self.xtream_username, 1, 1)
                self.layout.addWidget(self.xtream_password_label, 2, 0)
                self.layout.addWidget(self.xtream_password, 2, 1)
                self.layout.addWidget(self.xtream_url_label, 3, 0)
                self.layout.addWidget(self.xtream_url, 3, 1)
                i = 3
            i += 1
            first = True
            for _epg_edit in self.epg_edits:
                if first:
                    first = False
                    self.layout.addWidget(self.epg_label, i, 0)
                self.layout.addWidget(_epg_edit[0], i, 1)
                self.layout.addWidget(_epg_edit[1], i, 2)
                self.layout.addWidget(_epg_edit[2], i, 3)
                if len(_epg_edit) == 4:
                    self.layout.addWidget(_epg_edit[3], i, 4)
                i += 1
            self.layout.addWidget(self.more_settings, i, 1)
            i += 1
            if self.more_settings_shown:
                self.layout.addWidget(self.offset_label, i, 0)
                self.layout.addWidget(self.epg_offset_edit, i, 1)
                self.layout.addWidget(self.offset_label_hours, i, 2)
                i += 1
                self.layout.addWidget(self.useragent_label, i, 0)
                self.layout.addWidget(self.useragent_edit, i, 1)
                i += 1
                self.layout.addWidget(self.referer_label, i, 0)
                self.layout.addWidget(self.referer_edit, i, 1)
                i += 1
                if self.playlist_type == "local":
                    self.layout.addWidget(self.udp_proxy_label, i, 0)
                    self.layout.addWidget(self.udp_proxy_edit, i, 1)
                    i += 1
            self.layout.addWidget(self.save_btn, i + 3, 1)

        redraw_layout()

        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

    def on_save(self, overwrite=False):
        if self.playlist_type == "xtream":
            url = "XTREAM::::::::::::::" + "::::::::::::::".join(
                [
                    self.xtream_username.text().strip(),
                    self.xtream_password.text().strip(),
                    self.xtream_url.text().strip(),
                ]
            )
        elif self.playlist_type == "local":
            url = self.path_edit.text().strip()
        else:
            url = ""
        if not url:
            nourlset_msg = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Warning,
                "yuki-iptv",
                _("URL not specified!"),
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            nourlset_msg.exec()
        else:
            _name = os.path.basename(url)
            if url.startswith("XTREAM::::::::::::::"):
                _name = "XTream " + _("Playlist").lower()
            name = self.name_edit.text() if self.name_edit.text() else _name
            name = name if name else _("Playlist")
            epg = ",".join([_x[0].text() for _x in self.epg_edits])
            epg_offset = self.epg_offset_edit.value()
            playlist = {
                "m3u": url,
                "epg": epg,
                "epgoffset": epg_offset,
                "useragent": self.useragent_edit.text().strip(),
                "udp_proxy": self.udp_proxy_edit.text().strip(),
                "referer": self.referer_edit.text().strip(),
                "added": datetime.datetime.now().timestamp(),
            }

            if not overwrite and name in YukiData.playlists_saved:
                name = f"{name} "
            if self.old_name:
                YukiData.playlists_saved.pop(self.old_name)
            YukiData.playlists_saved[name] = playlist

            save_playlists()
            populate_playlists()

            self.close()
            Data.windows.remove(self)
            self.deleteLater()


def save_playlists():
    with open(
        str(Path(LOCAL_DIR, "playlists.json")), "w", encoding="utf8"
    ) as playlist_file:
        playlist_file.write(json.dumps(YukiData.playlists_saved))


def get_xtream_expiration_date(xt):
    xtream_exp_date = _("Unknown")
    try:
        xtream_exp_date = datetime.datetime.fromtimestamp(
            int(xt.auth_data["user_info"]["exp_date"])
        ).strftime("%x")
    except Exception:
        try:
            xtream_exp_date = str(xt.auth_data["user_info"]["exp_date"])
        except Exception:
            pass
    return xtream_exp_date


class XTream_list:
    data = []
    expiration = {}


def get_xtream_expiration_text(path):
    return _("Expiration date") + f": {XTream_list.expiration[path]}"


def xtream_playlists_set_icon(icon):
    for _i in range(Data.playlists_win.playlists_list.count()):
        item = Data.playlists_win.playlists_list.item(_i)
        _internal_name = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if _internal_name.startswith("playlist:"):
            _internal_name = _internal_name.replace("playlist:", "", 1)
            if _internal_name in YukiData.playlists_saved:
                if YukiData.playlists_saved[_internal_name]["m3u"] in XTream_list.data:
                    if not isinstance(icon, QtGui.QPixmap):
                        icon = icon.pixmap(32, 32)
                    Data.playlists_win.playlists_list.itemWidget(
                        item
                    ).icon_label.setPixmap(icon)


def show_xtream_playlists_expiration_set():
    for _i in range(Data.playlists_win.playlists_list.count()):
        item = Data.playlists_win.playlists_list.item(_i)
        _internal_name = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if _internal_name.startswith("playlist:"):
            _internal_name = _internal_name.replace("playlist:", "", 1)
            if _internal_name in YukiData.playlists_saved:
                path = YukiData.playlists_saved[_internal_name]["m3u"]
                if path in XTream_list.expiration:
                    widget = Data.playlists_win.playlists_list.itemWidget(item)
                    old_height = widget.description_label.sizeHint().height()
                    widget.description_label.setText(get_xtream_expiration_text(path))
                    widget.description_label.updateGeometry()
                    height_offset = (
                        widget.description_label.sizeHint().height() - old_height
                    )
                    item.setSizeHint(
                        QtCore.QSize(
                            Data.playlists_win.playlists_list.sizeHint().width(),
                            widget.sizeHint().height() + height_offset,
                        )
                    )


def xtream_playlists_show_loading():
    xtream_playlists_set_icon(YukiData.YukiGUI.loading_icon_small)


def xtream_playlists_hide_loading():
    xtream_playlists_set_icon(YukiData.YukiGUI.tv_icon)


def show_xtream_playlists_expiration():
    try:
        if not YukiData.xtream_list_lock:
            YukiData.xtream_list_lock = True
            xtream_data = []
            for playlist in YukiData.playlists_saved:
                path = YukiData.playlists_saved[playlist]["m3u"]
                if path.startswith("XTREAM::::::::::::::"):
                    xtream_data.append([path, YukiData.playlists_saved[playlist]])
            if xtream_data != XTream_list.data:
                XTream_list.data = xtream_data
                logger.info("Updating XTream expiration info")
                execute_in_main_thread(partial(xtream_playlists_show_loading))
                for xt_name in XTream_list.data:
                    headers = {}
                    if "useragent" in xt_name[1] and xt_name[1]["useragent"]:
                        headers["User-Agent"] = xt_name[1]["useragent"]
                    if "referer" in xt_name[1] and xt_name[1]["referer"]:
                        ref = xt_name[1]["referer"]
                        headers["Referer"] = ref
                        originURL = ""
                        if ref and ref.endswith("/"):
                            originURL = ref[:-1]
                        if originURL:
                            headers["Origin"] = originURL
                    if "User-Agent" not in headers:
                        headers["User-Agent"] = YukiData.settings["ua"]
                    if "Referer" not in headers:
                        headers["Referer"] = YukiData.settings["referer"]
                    xt, _xt_username, _xt_password, _xt_url = load_xtream(
                        xt_name[0], headers
                    )
                    XTream_list.expiration[xt_name[0]] = get_xtream_expiration_date(xt)
                execute_in_main_thread(partial(xtream_playlists_hide_loading))
                execute_in_main_thread(partial(show_xtream_playlists_expiration_set))
            YukiData.xtream_list_lock = False
    except Exception:
        logger.warning("Exception in show_xtream_playlists_expiration")
        logger.warning(traceback.format_exc())


def edit_playlist(playlist_name):
    if playlist_name in YukiData.playlists_saved:
        win = Playlists_Edit(YukiData.playlists_saved[playlist_name], playlist_name)
        Data.windows.append(win)
        win.show()
    else:
        show_exception(f"Playlist '{playlist_name}' not found in playlists!")


def delete_playlist(playlist_name):
    is_delete = QtWidgets.QMessageBox.question(
        None,
        "yuki-iptv",
        _("Delete playlist permanently?"),
        QtWidgets.QMessageBox.StandardButton.Yes
        | QtWidgets.QMessageBox.StandardButton.No,
        QtWidgets.QMessageBox.StandardButton.Yes,
    )
    if is_delete == QtWidgets.QMessageBox.StandardButton.Yes:
        YukiData.playlists_saved.pop(playlist_name)
        save_playlists()
        populate_playlists()


def playlist_selected(sel):
    if not isinstance(sel, str):
        sel = sel.data(QtCore.Qt.ItemDataRole.UserRole)
    if sel.startswith("internal:"):
        if sel == "internal:favourites_plus":
            favourites_plus()
        elif sel == "internal:no_playlists":
            add_playlist()
    elif sel.startswith("playlist:"):
        sel = sel.replace("playlist:", "", 1)
        if sel in YukiData.playlists_saved:
            playlist = YukiData.playlists_saved[sel]

            path = playlist["m3u"]
            epg = ""
            if "epg" in playlist and playlist["epg"]:
                epg = playlist["epg"]
            epg_offset = 0
            if "epgoffset" in playlist and playlist["epgoffset"]:
                epg_offset = playlist["epgoffset"]
            useragent = ""
            if "useragent" in playlist and playlist["useragent"]:
                useragent = playlist["useragent"]
            referer = ""
            if "referer" in playlist and playlist["referer"]:
                referer = playlist["referer"]
            udp_proxy = ""
            if "udp_proxy" in playlist and playlist["udp_proxy"]:
                udp_proxy = playlist["udp_proxy"]

            Data.playlists_win.close()
            YukiData.YukiGUI.m3u = path
            YukiData.YukiGUI.epg = epg
            YukiData.YukiGUI.soffset.setValue(epg_offset)
            YukiData.settings["playlist_useragent"] = useragent
            YukiData.settings["playlist_referer"] = referer
            YukiData.settings["playlist_udp_proxy"] = udp_proxy
            YukiData.save_settings()
        else:
            show_exception(f"Playlist '{sel}' not found in playlists!")


def populate_playlists():
    Data.playlists_win.playlists_list.clear()
    if YukiData.playlists_saved:
        # TODO: Global favourites
        # / Auto-generated playlist with aggregated favorites from all playlists
        with open(Path(LOCAL_DIR, "favplaylist.m3u"), "r") as favplaylist:
            if favplaylist.read() != "#EXTM3U\n#EXTINF:-1,-\nhttp://255.255.255.255\n":
                item = QtWidgets.QListWidgetItem()
                item.setData(
                    QtCore.Qt.ItemDataRole.UserRole, "internal:favourites_plus"
                )
                playlist_widget = PlaylistsWidget()
                playlist_widget.name_label.setText(_("Favourites+"))
                # playlist_widget.description_label.setText
                playlist_widget.btn_select.clicked.connect(
                    partial(playlist_selected, "internal:favourites_plus")
                )
                playlist_widget.btn_edit.hide()
                playlist_widget.btn_delete.hide()
                playlist_widget.icon_label.setPixmap(YukiData.YukiGUI.star_icon_pixmap)
                item.setSizeHint(
                    QtCore.QSize(
                        Data.playlists_win.playlists_list.sizeHint().width(),
                        playlist_widget.sizeHint().height(),
                    )
                )
                Data.playlists_win.playlists_list.addItem(item)
                Data.playlists_win.playlists_list.setItemWidget(item, playlist_widget)
        for playlist_name in YukiData.playlists_saved:
            if (
                YukiData.playlists_search.lower().strip()
                not in playlist_name.lower().strip()
            ):
                continue
            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.ItemDataRole.UserRole, f"playlist:{playlist_name}")
            playlist_widget = PlaylistsWidget()
            playlist_widget.name_label.setText(playlist_name)
            if "added" in YukiData.playlists_saved[playlist_name]:
                added_time = datetime.datetime.fromtimestamp(
                    YukiData.playlists_saved[playlist_name]["added"]
                ).strftime("%c")
                playlist_widget.description_label.setText(
                    _("Added") + f": {added_time}"
                )
            if YukiData.playlists_saved[playlist_name]["m3u"] in XTream_list.expiration:
                playlist_widget.description_label.setText(
                    get_xtream_expiration_text(
                        YukiData.playlists_saved[playlist_name]["m3u"]
                    )
                )
            playlist_widget.btn_select.clicked.connect(
                partial(playlist_selected, f"playlist:{playlist_name}")
            )
            playlist_widget.btn_edit.clicked.connect(
                partial(edit_playlist, playlist_name)
            )
            playlist_widget.btn_delete.clicked.connect(
                partial(delete_playlist, playlist_name)
            )
            item.setSizeHint(
                QtCore.QSize(
                    Data.playlists_win.playlists_list.sizeHint().width(),
                    playlist_widget.sizeHint().height(),
                )
            )
            Data.playlists_win.playlists_list.addItem(item)
            Data.playlists_win.playlists_list.setItemWidget(item, playlist_widget)
        if Data.playlists_win.playlists_list.count() == 0:
            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.ItemDataRole.UserRole, "internal:no_playlists_found")
            playlist_widget = PlaylistsWidget()
            playlist_widget.name_label.setText(_("No playlists were found"))
            playlist_widget.btn_select.clicked.connect(
                partial(playlist_selected, "internal:no_playlists_found")
            )
            playlist_widget.btn_select.hide()
            playlist_widget.btn_edit.hide()
            playlist_widget.btn_delete.hide()
            playlist_widget.icon_label.setPixmap(YukiData.YukiGUI.search_icon_pixmap)
            item.setSizeHint(
                QtCore.QSize(
                    Data.playlists_win.playlists_list.sizeHint().width(),
                    playlist_widget.sizeHint().height(),
                )
            )
            Data.playlists_win.playlists_list.addItem(item)
            Data.playlists_win.playlists_list.setItemWidget(item, playlist_widget)
        thread_show_xtream_playlists_expiration = threading.Thread(
            target=show_xtream_playlists_expiration, daemon=True
        )
        thread_show_xtream_playlists_expiration.start()
    else:
        item = QtWidgets.QListWidgetItem()
        item.setData(QtCore.Qt.ItemDataRole.UserRole, "internal:no_playlists")
        playlist_widget = PlaylistsWidget()
        playlist_widget.name_label.setText(_("No playlists were added"))
        playlist_widget.description_label.setText(_("Please add your first playlist"))
        playlist_widget.btn_select.clicked.connect(
            partial(playlist_selected, "internal:no_playlists")
        )
        playlist_widget.btn_select.hide()
        playlist_widget.btn_edit.hide()
        playlist_widget.btn_delete.hide()
        playlist_widget.icon_label.setPixmap(YukiData.YukiGUI.search_icon_pixmap)
        item.setSizeHint(
            QtCore.QSize(
                Data.playlists_win.playlists_list.sizeHint().width(),
                playlist_widget.sizeHint().height(),
            )
        )
        Data.playlists_win.playlists_list.addItem(item)
        Data.playlists_win.playlists_list.setItemWidget(item, playlist_widget)


def show_playlists():
    if not Data.playlists_win.isVisible():
        populate_playlists()
        move_window_to_center(Data.playlists_win)
        Data.playlists_win.show()
        Data.playlists_win.raise_()
        Data.playlists_win.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
        Data.playlists_win.activateWindow()
    else:
        Data.playlists_win.hide()
