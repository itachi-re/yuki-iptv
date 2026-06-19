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
import re
import sys
import json
import math
import time
import atexit
import locale
import signal
import urllib
import hashlib
import logging
import os.path
import datetime
import textwrap
import threading
import traceback
import subprocess
import urllib.parse
import yuki_iptv.environ  # noqa: F401
from pathlib import Path
from functools import partial
from gi.repository import Gio, GLib
from PyQt6 import QtGui, QtCore, QtWidgets
from multiprocessing import Manager, get_context, active_children
from yuki_iptv.qt_info import get_qt_info
from yuki_iptv.qt_exception import show_exception
from yuki_iptv.args import loglevel, parsed_args
from yuki_iptv.i18n import _, load_qt_translations
from yuki_iptv.kill_process_childs import kill_process_childs
from yuki_iptv.epg import (
    epg_worker,
    epg_is_in_date,
    worker_get_epg_id,
    worker_get_epg_icon,
    worker_get_all_epg_names,
    worker_get_epg_programmes,
    worker_get_current_programme,
    worker_check_programmes_actual,
)
from yuki_iptv.gui import YukiGUIClass, show_window, move_window_to_center
from yuki_iptv.xdg import CACHE_DIR, LOCAL_DIR, SAVE_FOLDER_DEFAULT
from yuki_iptv.misc import (
    WINDOW_SIZE,
    TVGUIDE_WIDTH,
    DOCKWIDGET_PLAYLIST_WIDTH,
    DOCKWIDGET_CONTROLPANEL_HEIGHT_LOW,
    DOCKWIDGET_CONTROLPANEL_HEIGHT_HIGH,
    YukiData,
    decode,
    convert_size,
    format_bytes,
    format_seconds,
    get_current_time,
)
from yuki_iptv.mpris import start_mpris, mpris_seeked, emit_mpris_change
from yuki_iptv.record import (
    record,
    init_record,
    stop_record,
    is_ffmpeg_recording,
    terminate_record_process,
)
from yuki_iptv.catchup import (
    get_catchup_url,
    format_catchup_array,
    parse_specifiers_in_url,
)
from yuki_iptv.inhibit import inhibit, register, uninhibit
from yuki_iptv.menubar import (
    get_seq,
    get_first_run,
    update_menubar,
    populate_menubar,
    init_menubar_player,
    get_active_vf_filters,
    init_yuki_iptv_menubar,
    reload_menubar_shortcuts,
)
from yuki_iptv.threads import execute_in_main_thread
from yuki_iptv.options import read_option, write_option
from yuki_iptv.keybinds import (
    main_keybinds_default,
    main_keybinds_internal,
    main_keybinds_translations,
)
from yuki_iptv.playlist import load_playlist
from yuki_iptv.mpv_options import get_mpv_options
from yuki_iptv.channel_logos import channel_logos_worker
from yuki_iptv.settings import parse_settings, get_epg_url
from yuki_iptv.gui_playlists import Data as gui_playlists_data
from yuki_iptv.gui_playlists import (
    show_playlists,
    playlist_selected,
    create_playlists_window,
)
from yuki_iptv.playlist_editor import PlaylistEditor
from yuki_iptv.stream_info import stream_info, open_stream_info, monitor_playback
from thirdparty import mpv

if sys.version_info < (3, 9, 0):
    show_exception("Python 3.9 or newer required")
    sys.exit(1)

logger = logging.getLogger("yuki-iptv")
mpv_logger = logging.getLogger("mpv")

APP_VERSION = "__DEB_VERSION__"

if parsed_args.version:
    print(f"yuki-iptv {APP_VERSION}")
    sys.exit(0)

Path(LOCAL_DIR).mkdir(parents=True, exist_ok=True)
Path(SAVE_FOLDER_DEFAULT).mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":

    def exit_handler(*args):
        try:
            try:
                if YukiData.epg_pool:
                    try:
                        YukiData.epg_pool.close()
                        YukiData.epg_pool = None
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                if multiprocessing_manager:
                    multiprocessing_manager.shutdown()
            except Exception:
                pass
            for process_3 in active_children():
                try:
                    process_3.kill()
                except Exception:
                    try:
                        process_3.terminate()
                    except Exception:
                        pass
            try:
                uninhibit()
            except Exception:
                pass
            try:
                for process_3 in active_children():
                    try:
                        process_3.kill()
                    except Exception:
                        try:
                            process_3.terminate()
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                stop_record()
            except Exception:
                pass
            try:
                for rec_1 in sch_recordings:
                    do_stop_record(rec_1)
            except Exception:
                pass
            try:
                if YukiData.mpris_loop:
                    YukiData.mpris_running = False
                    YukiData.mpris_loop.quit()
            except Exception:
                pass
            try:
                if multiprocessing_manager:
                    multiprocessing_manager.shutdown()
            except Exception:
                pass
            try:
                for process_3 in active_children():
                    try:
                        process_3.kill()
                    except Exception:
                        try:
                            process_3.terminate()
                        except Exception:
                            pass
            except Exception:
                pass
            if not YukiData.exiting:
                YukiData.exiting = True
                logger.info("Exiting")
            if not YukiData.do_save_settings:
                kill_process_childs(os.getpid())
        except BaseException:
            pass

    atexit.register(exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    signal.signal(signal.SIGINT, exit_handler)

    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()

    app.setDesktopFileName("yuki-iptv")
    load_qt_translations(app)

    # This is necessary since PyQT stomps over the locale settings needed by libmpv.
    # This needs to happen after importing PyQT before
    # creating the first mpv.MPV instance.
    locale.setlocale(locale.LC_NUMERIC, "C")

    try:
        logger.info(f"Version: {APP_VERSION}")
        logger.info(f"Python {sys.version.strip()}")
        logger.info(f"Qt {get_qt_info(app)}")

        multiprocessing_manager = Manager()
        YukiData.mp_manager_dict = multiprocessing_manager.dict()

        if not os.path.isfile(str(Path(LOCAL_DIR, "favplaylist.m3u"))):
            file01 = open(str(Path(LOCAL_DIR, "favplaylist.m3u")), "w", encoding="utf8")
            file01.write("#EXTM3U\n#EXTINF:-1,-\nhttp://255.255.255.255\n")
            file01.close()

        YukiData.channel_sets = {}

        def save_channel_sets():
            file2 = open(
                str(Path(LOCAL_DIR, "channelsettings.json")), "w", encoding="utf8"
            )
            file2.write(json.dumps(YukiData.channel_sets))
            file2.close()

        if not os.path.isfile(str(Path(LOCAL_DIR, "channelsettings.json"))):
            save_channel_sets()
        else:
            file1 = open(str(Path(LOCAL_DIR, "channelsettings.json")), encoding="utf8")
            YukiData.channel_sets = json.loads(file1.read())
            file1.close()

        YukiData.settings, settings_loaded = parse_settings()

        YukiData.favourite_sets = []

        def save_favourite_sets():
            favourite_sets_2 = {}
            if os.path.isfile(Path(LOCAL_DIR, "favouritechannels.json")):
                with open(
                    Path(LOCAL_DIR, "favouritechannels.json"), encoding="utf8"
                ) as fsetfile:
                    favourite_sets_2 = json.loads(fsetfile.read())
            if YukiData.settings["m3u"]:
                favourite_sets_2[YukiData.settings["m3u"]] = YukiData.favourite_sets
            file2 = open(
                Path(LOCAL_DIR, "favouritechannels.json"), "w", encoding="utf8"
            )
            file2.write(json.dumps(favourite_sets_2))
            file2.close()

        if not os.path.isfile(str(Path(LOCAL_DIR, "favouritechannels.json"))):
            save_favourite_sets()
        else:
            file1 = open(Path(LOCAL_DIR, "favouritechannels.json"), encoding="utf8")
            favourite_sets1 = json.loads(file1.read())
            if YukiData.settings["m3u"] in favourite_sets1:
                YukiData.favourite_sets = favourite_sets1[YukiData.settings["m3u"]]
            file1.close()

        YukiData.player_tracks = {}

        def save_player_tracks():
            player_tracks_2 = {}
            if os.path.isfile(Path(LOCAL_DIR, "tracks.json")):
                with open(
                    Path(LOCAL_DIR, "tracks.json"), encoding="utf8"
                ) as tracks_file0:
                    player_tracks_2 = json.loads(tracks_file0.read())
            if YukiData.settings["m3u"]:
                player_tracks_2[YukiData.settings["m3u"]] = YukiData.player_tracks
            tracks_file1 = open(Path(LOCAL_DIR, "tracks.json"), "w", encoding="utf8")
            tracks_file1.write(json.dumps(player_tracks_2))
            tracks_file1.close()

        if os.path.isfile(str(Path(LOCAL_DIR, "tracks.json"))):
            tracks_file = open(Path(LOCAL_DIR, "tracks.json"), encoding="utf8")
            player_tracks1 = json.loads(tracks_file.read())
            if YukiData.settings["m3u"] in player_tracks1:
                YukiData.player_tracks = player_tracks1[YukiData.settings["m3u"]]
            tracks_file.close()

        # https://www.qt.io/blog/dark-mode-on-windows-11-with-qt-6.5#before-qt-65
        current_palette = QtGui.QPalette()
        is_dark_theme = (
            current_palette.color(QtGui.QPalette.ColorRole.WindowText).lightness()
            > current_palette.color(QtGui.QPalette.ColorRole.Window).lightness()
        )
        if is_dark_theme:
            logger.info("Detected dark window theme")
            YukiData.use_dark_icon_theme = True
        else:
            YukiData.use_dark_icon_theme = False

        def get_epg_name(channel_name):
            epg_name = ""
            if (
                YukiData.settings["m3u"] in YukiData.channel_sets
                and channel_name in YukiData.channel_sets[YukiData.settings["m3u"]]
            ):
                if (
                    "epgname"
                    in YukiData.channel_sets[YukiData.settings["m3u"]][channel_name]
                ):
                    if YukiData.channel_sets[YukiData.settings["m3u"]][channel_name][
                        "epgname"
                    ]:
                        epg_name = YukiData.channel_sets[YukiData.settings["m3u"]][
                            channel_name
                        ]["epgname"]
            return epg_name

        def _get_epg_id(tvg_id, tvg_name, channel_name):
            ret = None
            if not YukiData.epg_pool_running:
                try:
                    ret = worker_get_epg_id(
                        tvg_id,
                        tvg_name,
                        channel_name,
                        get_epg_name(channel_name),
                        YukiData.epg_array,
                    )
                except Exception:
                    logger.warning("get_epg_id failed")
            return ret

        def get_epg_id(_data):
            if isinstance(_data, dict):
                _epg_title = (
                    _data["orig_title"] if "orig_title" in _data else _data["title"]
                )
                return _get_epg_id(_data["tvg-ID"], _data["tvg-name"], _epg_title)
            elif isinstance(_data, str):
                if _data in YukiData.array:
                    _epg_title = (
                        YukiData.array[_data]["orig_title"]
                        if "orig_title" in YukiData.array[_data]
                        else YukiData.array[_data]["title"]
                    )
                    return _get_epg_id(
                        YukiData.array[_data]["tvg-ID"],
                        YukiData.array[_data]["tvg-name"],
                        _epg_title,
                    )
                else:
                    return _get_epg_id("", "", _data)
            else:
                # logger.warning("get_epg_id failed - unknown type passed")
                return None

        def get_epg_programmes(epg_id):
            ret = None
            if not YukiData.epg_pool_running:
                try:
                    ret = worker_get_epg_programmes(epg_id, YukiData.epg_array)
                except Exception:
                    logger.warning("get_epg_programmes failed")
            return ret

        def get_epg_icon(epg_id):
            ret = None
            if not YukiData.epg_pool_running:
                try:
                    ret = worker_get_epg_icon(epg_id, YukiData.epg_array)
                except Exception:
                    logger.warning("get_epg_programmes failed")
            return ret

        def check_programmes_actual():
            ret = None
            if not YukiData.epg_pool_running:
                try:
                    ret = worker_check_programmes_actual(YukiData.epg_array)
                except Exception:
                    logger.warning("check_programmes_actual failed")
            return ret

        def get_all_epg_names():
            ret = None
            if not YukiData.epg_pool_running:
                try:
                    ret = worker_get_all_epg_names(YukiData.epg_array)
                except Exception:
                    logger.warning("get_all_epg_names failed")
            return ret

        def get_current_programme(epg_id):
            ret = None
            if not YukiData.epg_pool_running:
                try:
                    ret = worker_get_current_programme(epg_id, YukiData.epg_array)
                except Exception:
                    logger.warning("get_current_programme failed")
            return ret

        def purge_epg_cache():
            if not YukiData.epg_pool_running:
                logger.info("Purging EPG cache")
                for epg_cache_filename in os.listdir(Path(CACHE_DIR, "epg")):
                    epg_cache_file = Path(CACHE_DIR, "epg", epg_cache_filename)
                    if os.path.isfile(epg_cache_file):
                        os.remove(epg_cache_file)

        def force_update_epg_act():
            logger.info("Force update EPG triggered")
            purge_epg_cache()
            thread_epg_update_2 = threading.Thread(target=epg_update, daemon=True)
            thread_epg_update_2.start()

        def mainwindow_isvisible():
            try:
                return win.isVisible()
            except Exception:
                return False

        YukiGUI = YukiGUIClass()
        YukiData.YukiGUI = YukiGUI

        channels = {}

        playlist_editor = PlaylistEditor()

        def show_playlist_editor():
            if playlist_editor.isVisible():
                playlist_editor.hide()
            else:
                move_window_to_center(playlist_editor)
                playlist_editor.show()

        save_folder = YukiData.settings["save_folder"]

        if not os.path.isdir(str(Path(save_folder))):
            try:
                Path(save_folder).mkdir(parents=True, exist_ok=True)
            except Exception:
                logger.warning("Failed to create save folder!")
                show_exception("Failed to create save folder!")
                save_folder = SAVE_FOLDER_DEFAULT
                if not os.path.isdir(str(Path(save_folder))):
                    Path(save_folder).mkdir(parents=True, exist_ok=True)

        if not os.access(save_folder, os.W_OK | os.X_OK):
            save_folder = SAVE_FOLDER_DEFAULT
            logger.warning(
                "Save folder is not writable (os.access), using default save folder"
            )
            show_exception(
                "Save folder is not writable (os.access), using default save folder"
            )

        if not YukiData.settings["scrrecnosubfolders"]:
            try:
                Path(save_folder, "screenshots").mkdir(parents=True, exist_ok=True)
                Path(save_folder, "recordings").mkdir(parents=True, exist_ok=True)
            except Exception:
                save_folder = SAVE_FOLDER_DEFAULT
                logger.warning(
                    "Save folder is not writable (subfolders), "
                    "using default save folder"
                )
                show_exception(
                    "Save folder is not writable (subfolders), "
                    "using default save folder"
                )
        else:
            if os.path.isdir(str(Path(save_folder, "screenshots"))):
                try:
                    os.rmdir(str(Path(save_folder, "screenshots")))
                except Exception:
                    pass
            if os.path.isdir(str(Path(save_folder, "recordings"))):
                try:
                    os.rmdir(str(Path(save_folder, "recordings")))
                except Exception:
                    pass

        def getArrayItem(arr_item):
            arr_item_ret = None
            if arr_item:
                if arr_item in YukiData.array:
                    arr_item_ret = YukiData.array[arr_item]
                elif arr_item in YukiData.movies:
                    arr_item_ret = YukiData.movies[arr_item]
                else:
                    try:
                        if " ::: " in arr_item:
                            arr_item_split = arr_item.split(" ::: ")
                            for season_name in YukiData.series[
                                arr_item_split[2]
                            ].seasons.keys():
                                season = YukiData.series[arr_item_split[2]].seasons[
                                    season_name
                                ]
                                if season.name == arr_item_split[1]:
                                    for episode_name in season.episodes.keys():
                                        episode = season.episodes[episode_name]
                                        if episode.title == arr_item_split[0]:
                                            arr_item_ret = {
                                                "title": episode.title,
                                                "tvg-name": "",
                                                "tvg-ID": "",
                                                "tvg-logo": "",
                                                "tvg-group": _("All channels"),
                                                "tvg-url": "",
                                                "catchup": "default",
                                                "catchup-source": "",
                                                "catchup-days": "7",
                                                "useragent": "",
                                                "referer": "",
                                                "url": episode.url,
                                            }
                                            break
                                    break
                    except Exception:
                        logger.warning("Exception in getArrayItem (series)")
                        logger.warning(traceback.format_exc())
            return arr_item_ret

        if os.path.isfile(str(Path(LOCAL_DIR, "sortchannels.json"))):
            with open(
                str(Path(LOCAL_DIR, "sortchannels.json")), encoding="utf8"
            ) as channel_sort_file1:
                channel_sort3 = json.loads(channel_sort_file1.read())
                if YukiData.settings["m3u"] in channel_sort3:
                    YukiData.channel_sort = channel_sort3[YukiData.settings["m3u"]]

        groups, m3u_exists, xt = load_playlist()

        def sigint_handler(*args):
            if YukiData.mpris_loop:
                YukiData.mpris_running = False
                YukiData.mpris_loop.quit()
            app.quit()

        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)

        YukiGUI.create_windows()
        create_playlists_window()

        def resettodefaults_btn_clicked():
            resettodefaults_btn_clicked_msg = QtWidgets.QMessageBox.question(
                None,
                "yuki-iptv",
                _("Are you sure?"),
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes,
            )
            if (
                resettodefaults_btn_clicked_msg
                == QtWidgets.QMessageBox.StandardButton.Yes
            ):
                logger.info("Restoring default keybinds")
                YukiData.main_keybinds = main_keybinds_default.copy()
                YukiGUI.shortcuts_table.setRowCount(len(YukiData.main_keybinds))
                keybind_i = -1
                for keybind in YukiData.main_keybinds:
                    keybind_i += 1
                    YukiGUI.shortcuts_table.setItem(
                        keybind_i,
                        0,
                        get_widget_item(main_keybinds_translations[keybind]),
                    )
                    if isinstance(YukiData.main_keybinds[keybind], str):
                        keybind_str = YukiData.main_keybinds[keybind]
                    else:
                        keybind_str = QtGui.QKeySequence(
                            YukiData.main_keybinds[keybind]
                        ).toString()
                    kbd_widget = get_widget_item(keybind_str)
                    kbd_widget.setToolTip(_("Double click to change"))
                    YukiGUI.shortcuts_table.setItem(keybind_i, 1, kbd_widget)
                YukiGUI.shortcuts_table.resizeColumnsToContents()
                hotkeys_file_1 = open(
                    str(Path(LOCAL_DIR, "hotkeys.json")), "w", encoding="utf8"
                )
                hotkeys_file_1.write(
                    json.dumps({"current_profile": {"keys": YukiData.main_keybinds}})
                )
                hotkeys_file_1.close()
                reload_keybinds()

        YukiGUI.resettodefaults_btn.clicked.connect(resettodefaults_btn_clicked)

        class KeySequenceEdit(QtWidgets.QKeySequenceEdit):
            def keyPressEvent(self, event):
                super().keyPressEvent(event)
                self.setKeySequence(QtGui.QKeySequence(self.keySequence()))

        YukiGUI.keyseq = KeySequenceEdit()

        def keyseq_ok_clicked():
            if YukiData.selected_shortcut_row != -1:
                sel_keyseq = YukiGUI.keyseq.keySequence().toString()
                search_value = YukiGUI.shortcuts_table.item(
                    YukiData.selected_shortcut_row, 0
                ).text()
                shortcut_taken = False
                for sci1 in range(YukiGUI.shortcuts_table.rowCount()):
                    if sci1 != YukiData.selected_shortcut_row:
                        if YukiGUI.shortcuts_table.item(sci1, 1).text() == sel_keyseq:
                            shortcut_taken = True
                forbidden_hotkeys = [
                    "Return",
                    "Key.Key_MediaNext",
                    "Key.Key_MediaPause",
                    "Key.Key_MediaPlay",
                    "Key.Key_MediaPrevious",
                    "Key.Key_MediaRecord",
                    "Key.Key_MediaStop",
                    "Key.Key_MediaTogglePlayPause",
                    "Key.Key_Play",
                    "Key.Key_Stop",
                    "Key.Key_VolumeDown",
                    "Key.Key_VolumeMute",
                    "Key.Key_VolumeUp",
                ]
                if sel_keyseq in forbidden_hotkeys:
                    shortcut_taken = True
                if not shortcut_taken:
                    YukiGUI.shortcuts_table.item(
                        YukiData.selected_shortcut_row, 1
                    ).setText(sel_keyseq)
                    for name55, value55 in main_keybinds_translations.items():
                        if value55 == search_value:
                            YukiData.main_keybinds[name55] = sel_keyseq
                            hotkeys_file = open(
                                str(Path(LOCAL_DIR, "hotkeys.json")),
                                "w",
                                encoding="utf8",
                            )
                            hotkeys_file.write(
                                json.dumps(
                                    {
                                        "current_profile": {
                                            "keys": YukiData.main_keybinds
                                        }
                                    }
                                )
                            )
                            hotkeys_file.close()
                            reload_keybinds()
                    YukiGUI.shortcuts_win_2.hide()
                else:
                    msg_shortcut_taken = QtWidgets.QMessageBox(
                        QtWidgets.QMessageBox.Icon.Warning,
                        "yuki-iptv",
                        _("Shortcut already used"),
                        QtWidgets.QMessageBox.StandardButton.Ok,
                    )
                    msg_shortcut_taken.exec()

        def epg_win_checkbox_changed():
            YukiGUI.tvguide_lbl_2.verticalScrollBar().setSliderPosition(
                YukiGUI.tvguide_lbl_2.verticalScrollBar().minimum()
            )
            YukiGUI.tvguide_lbl_2.setText(_("No TV guide for channel"))
            try:
                ch_3 = YukiGUI.epg_win_checkbox.currentText()
                ch_3_guide = update_tvguide(
                    ch_3, True, date_selected=YukiData.epg_selected_date
                ).replace("!@#$%^^&*(", "\n")
                ch_3_guide = ch_3_guide.replace("\n", "<br>").replace("<br>", "", 1)
                if ch_3_guide.strip():
                    YukiGUI.tvguide_lbl_2.setText(ch_3_guide)
                else:
                    YukiGUI.tvguide_lbl_2.setText(_("No TV guide for channel"))
            except Exception:
                exc = traceback.format_exc()
                logger.warning("Exception in epg_win_checkbox_changed")
                logger.warning(exc)
                show_exception(exc)

        def showonlychplaylist_chk_clk():
            update_tvguide_2()

        def tvguide_channelfilter_do():
            try:
                filter_txt3 = YukiGUI.tvguidechannelfilter.text()
            except Exception:
                filter_txt3 = ""
            for item6 in range(YukiGUI.epg_win_checkbox.count()):
                if (
                    filter_txt3.lower().strip()
                    in YukiGUI.epg_win_checkbox.itemText(item6).lower().strip()
                ):
                    YukiGUI.epg_win_checkbox.view().setRowHidden(item6, False)
                else:
                    YukiGUI.epg_win_checkbox.view().setRowHidden(item6, True)

        def epg_date_changed(epg_date):
            YukiData.epg_selected_date = datetime.datetime.fromordinal(
                epg_date.toPyDate().toordinal()
            )
            epg_win_checkbox_changed()

        YukiData.archive_epg = None

        def do_open_archive(link):
            if "#__archive__" in link:
                archive_json = json.loads(
                    urllib.parse.unquote_plus(link.split("#__archive__")[1])
                )
                arr1 = getArrayItem(archive_json[0])
                arr1 = format_catchup_array(arr1)

                channel_url = getArrayItem(archive_json[0])["url"]
                start_time = archive_json[1]
                end_time = archive_json[2]
                prog_index = archive_json[3]

                if "#__rewind__" not in link:
                    YukiData.archive_epg = archive_json

                catchup_id = ""
                try:
                    current_programmes = None
                    epg_id = get_epg_id(archive_json[0])
                    if epg_id:
                        programmes = get_epg_programmes(epg_id)
                        if programmes:
                            current_programmes = programmes

                    if current_programmes:
                        if "catchup-id" in current_programmes[int(prog_index)]:
                            catchup_id = current_programmes[int(prog_index)][
                                "catchup-id"
                            ]
                except Exception:
                    logger.warning("do_open_archive / catchup_id parsing failed")
                    logger.warning(traceback.format_exc())

                arr2 = arr1

                if YukiData.is_xtream:
                    arr2["catchup"] = "xc"

                play_url = get_catchup_url(
                    channel_url, arr2, start_time, end_time, catchup_id
                )

                itemClicked_event(
                    archive_json[0], play_url, True, is_rewind=(len(archive_json) == 5)
                )
                setChannelText("({}) {}".format(_("Archive"), archive_json[0]), True)
                YukiGUI.progress.hide()
                YukiGUI.start_label.setText("")
                YukiGUI.start_label.hide()
                YukiGUI.stop_label.setText("")
                YukiGUI.stop_label.hide()
                YukiGUI.epg_win.hide()

                return False

        def esw_input_edit():
            esw_input_text = YukiGUI.esw_input.text().lower()
            for est_w in range(0, YukiGUI.esw_select.count()):
                if (
                    YukiGUI.esw_select.item(est_w)
                    .text()
                    .lower()
                    .startswith(esw_input_text)
                ):
                    YukiGUI.esw_select.item(est_w).setHidden(False)
                else:
                    YukiGUI.esw_select.item(est_w).setHidden(True)

        def esw_select_clicked(item1):
            YukiGUI.epg_select_win.hide()
            if item1.text():
                YukiGUI.epgname_lbl.setText(item1.text())
            else:
                YukiGUI.epgname_lbl.setText(_("Default"))

        def ext_open_btn_clicked():
            write_option("extplayer", YukiGUI.ext_player_txt.text().strip())
            YukiGUI.ext_win.close()
            try:
                subprocess.Popen(
                    YukiGUI.ext_player_txt.text().strip().split(" ")
                    + [getArrayItem(YukiData.item_selected)["url"]]
                )
            except Exception:
                logger.warning("Failed to open external player!")
                logger.warning(traceback.format_exc())
                show_exception(
                    traceback.format_exc(), _("Failed to open external player!")
                )

        YukiGUI.create4()

        YukiData.epg_selected_date = datetime.datetime.fromordinal(
            datetime.date.today().toordinal()
        )

        YukiGUI.keyseq_cancel.clicked.connect(YukiGUI.shortcuts_win_2.hide)
        YukiGUI.keyseq_ok.clicked.connect(keyseq_ok_clicked)
        YukiGUI.tvguidechannelfiltersearch.clicked.connect(tvguide_channelfilter_do)
        YukiGUI.tvguidechannelfilter.returnPressed.connect(tvguide_channelfilter_do)
        YukiGUI.showonlychplaylist_chk.clicked.connect(showonlychplaylist_chk_clk)
        YukiGUI.epg_win_checkbox.currentIndexChanged.connect(epg_win_checkbox_changed)
        YukiGUI.epg_select_date.activated.connect(epg_date_changed)
        YukiGUI.epg_select_date.clicked.connect(epg_date_changed)
        YukiGUI.tvguide_lbl_2.label.linkActivated.connect(do_open_archive)
        YukiGUI.esw_button.clicked.connect(esw_input_edit)
        YukiGUI.esw_select.itemDoubleClicked.connect(esw_select_clicked)
        YukiGUI.ext_open_btn.clicked.connect(ext_open_btn_clicked)

        extplayer = read_option("extplayer")
        if extplayer is None:
            extplayer = "mpv"
        YukiGUI.ext_player_txt.setText(extplayer)

        YukiData.playlists_saved = {}

        if os.path.isfile(str(Path(LOCAL_DIR, "playlists.json"))):
            playlists_json = open(
                str(Path(LOCAL_DIR, "playlists.json")), encoding="utf8"
            )
            YukiData.playlists_saved = json.loads(playlists_json.read())
            playlists_json.close()

        YukiData.time_stop = 0

        YukiData.ffmpeg_processes = []

        init_record(show_exception, YukiData.ffmpeg_processes)

        def convert_time(times_1):
            yr = time.strftime("%Y", time.localtime())
            yr = yr[0] + yr[1]
            times_1_sp = times_1.split(" ")
            times_1_sp_0 = times_1_sp[0].split(".")
            times_1_sp_0[2] = yr + times_1_sp_0[2]
            times_1_sp[0] = ".".join(times_1_sp_0)
            return " ".join(times_1_sp)

        def programme_clicked(item):
            times = item.text().split("\n")[0]
            start_time = convert_time(times.split(" - ")[0])
            end_time = convert_time(times.split(" - ")[1])
            YukiGUI.starttime_w.setDateTime(
                QtCore.QDateTime.fromString(start_time, "d.M.yyyy hh:mm")
            )
            YukiGUI.endtime_w.setDateTime(
                QtCore.QDateTime.fromString(end_time, "d.M.yyyy hh:mm")
            )

        def addrecord_clicked():
            selected_channel = YukiGUI.choosechannel_ch.currentText()
            start_time_r = (
                YukiGUI.starttime_w.dateTime().toPyDateTime().strftime("%d.%m.%y %H:%M")
            )
            end_time_r = (
                YukiGUI.endtime_w.dateTime().toPyDateTime().strftime("%d.%m.%y %H:%M")
            )
            YukiGUI.schedulers.addItem(
                _("Channel") + ": " + selected_channel + "\n"
                "{}: ".format(_("Start record time")) + start_time_r + "\n"
                "{}: ".format(_("End record time")) + end_time_r + "\n"
            )

        sch_recordings = {}

        def do_start_record(name1):
            ch_name = name1.split("_")[0]
            ch = ch_name.replace(" ", "_")
            for char in FORBIDDEN_CHARS:
                ch = ch.replace(char, "")
            cur_time = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
            if not YukiData.settings["scrrecnosubfolders"]:
                out_file = str(
                    Path(
                        save_folder,
                        "recordings",
                        f"recording_-_{cur_time}_-_{ch}.ts",
                    )
                )
            else:
                out_file = str(
                    Path(
                        save_folder,
                        f"recording_-_{cur_time}_-_{ch}.ts",
                    )
                )
            return [
                record(
                    getArrayItem(ch_name)["url"],
                    out_file,
                    ch_name,
                    f"Referer: {YukiData.settings['referer']}",
                    get_ua_ref_for_channel,
                    True,
                ),
                time.time(),
                out_file,
                ch_name,
            ]

        def do_stop_record(name2):
            if name2 in sch_recordings:
                ffmpeg_process = sch_recordings[name2][0]
                if ffmpeg_process:
                    terminate_record_process(ffmpeg_process)

        def record_post_action_after():
            logger.info("Record via scheduler ended, executing post-action...")
            # 0 - nothing to do
            if YukiGUI.praction_choose.currentIndex() == 1:  # 1 - Press Stop
                mpv_stop()

        def record_post_action():
            while True:
                if is_recording_func() is True:
                    break
                time.sleep(1)
            execute_in_main_thread(partial(record_post_action_after))

        def record_timer_2():
            try:
                activerec_list_value = (
                    YukiGUI.activerec_list.verticalScrollBar().value()
                )
                YukiGUI.activerec_list.clear()
                for sch0 in sch_recordings:
                    counted_time0 = format_seconds(
                        time.time() - sch_recordings[sch0][1]
                    )
                    channel_name0 = sch_recordings[sch0][3]
                    file_name0 = sch_recordings[sch0][2]
                    file_size0 = "WAITING"
                    if os.path.isfile(file_name0):
                        file_size0 = convert_size(os.path.getsize(file_name0))
                    YukiGUI.activerec_list.addItem(
                        channel_name0 + "\n" + counted_time0 + " " + file_size0
                    )
                YukiGUI.activerec_list.verticalScrollBar().setValue(
                    activerec_list_value
                )
                pl_text = "REC / " + _("Scheduler")
                if YukiGUI.activerec_list.count() != 0:
                    YukiData.recViaScheduler = True
                    YukiGUI.lbl2.setText(pl_text)
                    YukiGUI.lbl2.show()
                else:
                    if YukiData.recViaScheduler:
                        logger.info(
                            "Record via scheduler ended, waiting"
                            " for ffmpeg process completion..."
                        )
                        thread_record_post_action = threading.Thread(
                            target=record_post_action, daemon=True
                        )
                        thread_record_post_action.start()
                    YukiData.recViaScheduler = False
                    if YukiGUI.lbl2.text() == pl_text:
                        YukiGUI.lbl2.hide()
            except Exception:
                pass

        def record_timer():
            try:
                if YukiData.is_recording != YukiData.is_recording_old:
                    YukiData.is_recording_old = YukiData.is_recording
                    if YukiData.is_recording:
                        execute_in_main_thread(
                            partial(
                                YukiGUI.btn_record.setIcon, YukiGUI.record_stop_icon
                            )
                        )
                    else:
                        execute_in_main_thread(
                            partial(YukiGUI.btn_record.setIcon, YukiGUI.record_icon)
                        )
                status = _("No planned recordings")
                sch_items = [
                    str(YukiGUI.schedulers.item(i1).text())
                    for i1 in range(YukiGUI.schedulers.count())
                ]
                i3 = -1
                for sch_item in sch_items:
                    i3 += 1
                    status = _("Waiting for record")
                    sch_item = [i2.split(": ")[1] for i2 in sch_item.split("\n") if i2]
                    channel_name_rec = sch_item[0]
                    current_time = time.strftime("%d.%m.%y %H:%M", time.localtime())
                    start_time_1 = sch_item[1]
                    end_time_1 = sch_item[2]
                    array_name = (
                        str(channel_name_rec)
                        + "_"
                        + str(start_time_1)
                        + "_"
                        + str(end_time_1)
                    )
                    if start_time_1 == current_time:
                        if array_name not in sch_recordings:
                            st_planned = (
                                "Starting planned record"
                                + " (start_time='{}' end_time='{}' channel='{}')"
                            )
                            logger.info(
                                st_planned.format(
                                    start_time_1, end_time_1, channel_name_rec
                                )
                            )
                            sch_recordings[array_name] = do_start_record(array_name)
                            YukiData.ffmpeg_processes.append(sch_recordings[array_name])
                    if end_time_1 == current_time:
                        if array_name in sch_recordings:
                            YukiGUI.schedulers.takeItem(i3)
                            stop_planned = (
                                "Stopping planned record"
                                + " (start_time='{}' end_time='{}' channel='{}')"
                            )
                            logger.info(
                                stop_planned.format(
                                    start_time_1, end_time_1, channel_name_rec
                                )
                            )
                            do_stop_record(array_name)
                            sch_recordings.pop(array_name)
                    if sch_recordings:
                        status = _("Recording")
                YukiGUI.statusrec_lbl.setText("{}: {}".format(_("Status"), status))
            except Exception:
                pass

        def delrecord_clicked():
            schCurrentRow = YukiGUI.schedulers.currentRow()
            if schCurrentRow != -1:
                sch_index = "_".join(
                    [
                        xs.split(": ")[1]
                        for xs in YukiGUI.schedulers.item(schCurrentRow)
                        .text()
                        .split("\n")
                        if xs
                    ]
                )
                YukiGUI.schedulers.takeItem(schCurrentRow)
                if sch_index in sch_recordings:
                    do_stop_record(sch_index)
                    sch_recordings.pop(sch_index)

        def scheduler_channelfilter_do():
            try:
                filter_txt2 = YukiGUI.schedulerchannelfilter.text()
            except Exception:
                filter_txt2 = ""
            for item5 in range(YukiGUI.choosechannel_ch.count()):
                if (
                    filter_txt2.lower().strip()
                    in YukiGUI.choosechannel_ch.itemText(item5).lower().strip()
                ):
                    YukiGUI.choosechannel_ch.view().setRowHidden(item5, False)
                else:
                    YukiGUI.choosechannel_ch.view().setRowHidden(item5, True)

        YukiGUI.create_scheduler_widgets(get_current_time())

        def save_sort():
            YukiData.channel_sort = [
                YukiGUI.sort_list.item(z0).text()
                for z0 in range(YukiGUI.sort_list.count())
            ]
            channel_sort2 = {}
            if os.path.isfile(Path(LOCAL_DIR, "sortchannels.json")):
                with open(
                    Path(LOCAL_DIR, "sortchannels.json"), encoding="utf8"
                ) as file5:
                    channel_sort2 = json.loads(file5.read())
            channel_sort2[YukiData.settings["m3u"]] = YukiData.channel_sort
            with open(
                Path(LOCAL_DIR, "sortchannels.json"), "w", encoding="utf8"
            ) as channel_sort_file:
                channel_sort_file.write(json.dumps(channel_sort2))
            YukiGUI.sort_win.hide()

        YukiGUI.create_sort_widgets()
        YukiGUI.save_sort_btn.clicked.connect(save_sort)

        YukiGUI.tvguide_sch.itemClicked.connect(programme_clicked)
        YukiGUI.addrecord_btn.clicked.connect(addrecord_clicked)
        YukiGUI.delrecord_btn.clicked.connect(delrecord_clicked)
        YukiGUI.schedulerchannelfiltersearch.clicked.connect(scheduler_channelfilter_do)
        YukiGUI.schedulerchannelfilter.returnPressed.connect(scheduler_channelfilter_do)

        def save_folder_select():
            folder_name = QtWidgets.QFileDialog.getExistingDirectory(
                YukiGUI.settings_win,
                _("Select folder for recordings and screenshots"),
                options=QtWidgets.QFileDialog.Option.ShowDirsOnly,
            )
            if folder_name:
                YukiGUI.save_folder_widget.setText(folder_name)

        # Channel settings window
        def epgname_btn_action():
            prog_ids_0 = get_all_epg_names()
            if not prog_ids_0:
                prog_ids_0 = set()
            YukiGUI.esw_select.clear()
            YukiGUI.esw_select.addItem("")
            for prog_ids_0_dat in prog_ids_0:
                YukiGUI.esw_select.addItem(prog_ids_0_dat)
            esw_input_edit()
            move_window_to_center(YukiGUI.epg_select_win)
            YukiGUI.epg_select_win.show()

        YukiGUI.epgname_btn.clicked.connect(epgname_btn_action)

        default_user_agent = (
            YukiData.settings["playlist_useragent"]
            if YukiData.settings["playlist_useragent"]
            else YukiData.settings["ua"]
        )
        logger.info(f"Default User-Agent: {default_user_agent}")
        default_referer = (
            YukiData.settings["playlist_referer"]
            if YukiData.settings["playlist_referer"]
            else YukiData.settings["referer"]
        )
        if default_referer:
            logger.info(f"Default HTTP referer: {default_referer}")
        else:
            logger.info("Default HTTP referer: (empty)")

        def hideLoading():
            YukiData.is_loading = False
            loading.hide()
            YukiGUI.loading_movie.stop()
            YukiGUI.loading1.hide()
            execute_in_main_thread(partial(idle_on_metadata))

        def showLoading():
            YukiData.is_loading = True
            YukiGUI.centerwidget(YukiGUI.loading1)
            loading.show()
            YukiGUI.loading_movie.start()
            YukiGUI.loading1.show()
            execute_in_main_thread(partial(idle_on_metadata))

        def on_before_play():
            YukiGUI.streaminfo_win.hide()
            stream_info.video_properties.clear()
            stream_info.video_properties[_("General")] = {}
            stream_info.video_properties[_("Color")] = {}

            stream_info.audio_properties.clear()
            stream_info.audio_properties[_("General")] = {}
            stream_info.audio_properties[_("Layout")] = {}

            stream_info.video_bitrates.clear()
            stream_info.audio_bitrates.clear()

        def get_ua_ref_for_channel(channel_name1):
            useragent_ref = (
                YukiData.settings["playlist_useragent"]
                if YukiData.settings["playlist_useragent"]
                else YukiData.settings["ua"]
            )
            referer_ref = (
                YukiData.settings["playlist_referer"]
                if YukiData.settings["playlist_referer"]
                else YukiData.settings["referer"]
            )
            if channel_name1:
                channel_item = getArrayItem(channel_name1)
                if channel_item:
                    useragent_ref = (
                        channel_item["useragent"]
                        if "useragent" in channel_item and channel_item["useragent"]
                        else (
                            YukiData.settings["playlist_useragent"]
                            if YukiData.settings["playlist_useragent"]
                            else YukiData.settings["ua"]
                        )
                    )
                    referer_ref = (
                        channel_item["referer"]
                        if "referer" in channel_item and channel_item["referer"]
                        else (
                            YukiData.settings["playlist_referer"]
                            if YukiData.settings["playlist_referer"]
                            else YukiData.settings["referer"]
                        )
                    )
            if YukiData.settings["m3u"] in YukiData.channel_sets:
                channel_set = YukiData.channel_sets[YukiData.settings["m3u"]]
                if channel_name1 and channel_name1 in channel_set:
                    channel_config = channel_set[channel_name1]
                    if (
                        "ua" in channel_config
                        and channel_config["ua"]
                        and channel_config["ua"]
                        != (
                            YukiData.settings["playlist_useragent"]
                            if YukiData.settings["playlist_useragent"]
                            else YukiData.settings["ua"]
                        )
                    ):
                        useragent_ref = channel_config["ua"]
                    if (
                        "ref" in channel_config
                        and channel_config["ref"]
                        and channel_config["ref"]
                        != (
                            YukiData.settings["playlist_referer"]
                            if YukiData.settings["playlist_referer"]
                            else YukiData.settings["referer"]
                        )
                    ):
                        referer_ref = channel_config["ref"]
            return useragent_ref, referer_ref

        def mpv_override_play(arg_override_play, channel_name1=""):
            on_before_play()
            useragent_ref, referer_ref = get_ua_ref_for_channel(channel_name1)
            YukiData.player.user_agent = useragent_ref
            if referer_ref:
                originURL = ""
                if referer_ref.endswith("/"):
                    originURL = referer_ref[:-1]
                if originURL:
                    YukiData.player.http_header_fields = (
                        f"Referer: {referer_ref},Origin: {originURL}"
                    )
                else:
                    YukiData.player.http_header_fields = f"Referer: {referer_ref}"
            else:
                YukiData.player.http_header_fields = ""

            if not arg_override_play.endswith("/main.png"):
                logger.info(f"Using User-Agent: {YukiData.player.user_agent}")
                cur_ref = ""
                try:
                    for ref1 in YukiData.player.http_header_fields:
                        if ref1.startswith("Referer: "):
                            ref1 = ref1.replace("Referer: ", "", 1)
                            cur_ref = ref1
                except Exception:
                    pass
                if cur_ref:
                    logger.info(f"Using HTTP Referer: {cur_ref}")
                else:
                    logger.info("Using HTTP Referer: (empty)")

            YukiData.player.pause = False
            YukiData.player.play(parse_specifiers_in_url(arg_override_play))
            if YukiData.event_handler:
                try:
                    YukiData.event_handler.on_metadata()
                except Exception:
                    pass

        def mpv_override_stop(ignore=False):
            YukiData.player.command("stop")
            if not ignore:
                logger.info("Disabling deinterlace for main.png")
                YukiData.player.deinterlace = False
            YukiData.player.play(str(Path(YukiGUI.icons_folder, "main.png")))
            YukiData.player.pause = True
            if YukiData.event_handler:
                try:
                    YukiData.event_handler.on_metadata()
                except Exception:
                    pass

        def mpv_override_volume(volume_val):
            YukiData.player.volume = volume_val
            YukiData.volume = volume_val
            if YukiData.event_handler:
                try:
                    YukiData.event_handler.on_volume()
                except Exception:
                    pass

        def mpv_override_mute(mute_val):
            YukiData.player.mute = mute_val
            if YukiData.event_handler:
                try:
                    YukiData.event_handler.on_volume()
                except Exception:
                    pass

        def stopPlayer(ignore=False):
            try:
                mpv_override_stop(ignore)
            except Exception:
                YukiData.player.loop = True
                mpv_override_play(str(Path(YukiGUI.icons_folder, "main.png")))
                YukiData.player.pause = True

        def setVideoAspect(va):
            if va == 0:
                va = -1
            try:
                YukiData.player.video_aspect_override = va
            except Exception:
                YukiData.player.video_aspect = va

        def getVideoAspect():
            try:
                va1 = YukiData.player.video_aspect_override
            except Exception:
                va1 = YukiData.player.video_aspect
            return va1

        def doPlay(play_url1, ua_ch=default_user_agent, channel_name_0=""):
            YukiData.do_play_args = (play_url1, ua_ch, channel_name_0)
            logger.info(f"Playing channel: {channel_name_0}")
            logger.debug(f"URL: {play_url1}")
            loading.setText(_("Loading..."))
            loading.setFont(YukiGUI.font_italic_medium)
            showLoading()
            YukiData.player.loop = False
            mpv_override_play(play_url1, channel_name_0)
            thread_set_player_settings = threading.Thread(
                target=set_player_settings, args=(channel_name_0,), daemon=True
            )
            thread_set_player_settings.start()
            thread_monitor_playback = threading.Thread(
                target=monitor_playback, daemon=True
            )
            thread_monitor_playback.start()

        def channel_settings_save():
            channel_3 = YukiGUI.title.text()
            if YukiData.settings["m3u"] not in YukiData.channel_sets:
                YukiData.channel_sets[YukiData.settings["m3u"]] = {}
            YukiData.channel_sets[YukiData.settings["m3u"]][channel_3] = {
                "deinterlace": YukiGUI.deinterlace_chk.isChecked(),
                "ua": YukiGUI.useragent_choose.text(),
                "ref": YukiGUI.referer_choose_custom.text(),
                "group": YukiGUI.group_text.text(),
                "hidden": YukiGUI.hidden_chk.isChecked(),
                "contrast": YukiGUI.contrast_choose.value(),
                "brightness": YukiGUI.brightness_choose.value(),
                "hue": YukiGUI.hue_choose.value(),
                "saturation": YukiGUI.saturation_choose.value(),
                "gamma": YukiGUI.gamma_choose.value(),
                "videoaspect": YukiGUI.videoaspect_choose.currentIndex(),
                "zoom": YukiGUI.zoom_choose.currentIndex(),
                "panscan": YukiGUI.panscan_choose.value(),
                "epgname": (
                    YukiGUI.epgname_lbl.text()
                    if YukiGUI.epgname_lbl.text() != _("Default")
                    else ""
                ),
            }
            save_channel_sets()
            if YukiData.playing_channel == channel_3:
                YukiData.player.deinterlace = YukiGUI.deinterlace_chk.isChecked()
                YukiData.player.contrast = YukiGUI.contrast_choose.value()
                YukiData.player.brightness = YukiGUI.brightness_choose.value()
                YukiData.player.hue = YukiGUI.hue_choose.value()
                YukiData.player.saturation = YukiGUI.saturation_choose.value()
                YukiData.player.gamma = YukiGUI.gamma_choose.value()
                YukiData.player.video_zoom = YukiGUI.zoom_vars[
                    list(YukiGUI.zoom_vars)[YukiGUI.zoom_choose.currentIndex()]
                ]
                YukiData.player.panscan = YukiGUI.panscan_choose.value()
                setVideoAspect(
                    YukiGUI.videoaspect_vars[
                        list(YukiGUI.videoaspect_vars)[
                            YukiGUI.videoaspect_choose.currentIndex()
                        ]
                    ]
                )
            execute_in_main_thread(partial(redraw_channels))
            YukiGUI.channels_win.close()

        YukiGUI.save_btn.clicked.connect(channel_settings_save)

        YukiGUI.channels_win.setCentralWidget(YukiGUI.wid)

        def save_settings():
            settings_arr = YukiGUI.get_settings()
            with open(
                str(Path(LOCAL_DIR, "settings.json")), "w", encoding="utf8"
            ) as settings_file:
                settings_file.write(json.dumps(settings_arr))
            YukiGUI.settings_win.hide()
            YukiData.do_save_settings = True
            app.quit()

        YukiData.save_settings = save_settings

        def reset_channel_settings():
            if os.path.isfile(str(Path(LOCAL_DIR, "channelsettings.json"))):
                os.remove(str(Path(LOCAL_DIR, "channelsettings.json")))
            if os.path.isfile(str(Path(LOCAL_DIR, "favouritechannels.json"))):
                os.remove(str(Path(LOCAL_DIR, "favouritechannels.json")))
            if os.path.isfile(str(Path(LOCAL_DIR, "sortchannels.json"))):
                os.remove(str(Path(LOCAL_DIR, "sortchannels.json")))
            save_settings()

        def do_clear_logo_cache():
            logger.info("Clearing channel logos cache...")
            if os.path.isdir(Path(CACHE_DIR, "logo")):
                channel_logos = os.listdir(Path(CACHE_DIR, "logo"))
                for channel_logo in channel_logos:
                    if os.path.isfile(Path(CACHE_DIR, "logo", channel_logo)):
                        os.remove(Path(CACHE_DIR, "logo", channel_logo))
            logger.info("Channel logos cache cleared!")

        def close_settings():
            YukiGUI.settings_win.hide()
            if not win.isVisible():
                if not gui_playlists_data.playlists_win.isVisible():
                    myExitHandler_before()
                    sys.exit(0)

        YukiGUI.ssave.clicked.connect(save_settings)
        YukiGUI.sreset.clicked.connect(reset_channel_settings)
        YukiGUI.clear_logo_cache.clicked.connect(do_clear_logo_cache)
        YukiGUI.sclose.clicked.connect(close_settings)
        YukiGUI.sfolder.clicked.connect(save_folder_select)

        YukiGUI.set_from_settings()

        YukiGUI.settings_win.scroll.setWidget(YukiGUI.wid2)

        def set_url_text():
            YukiGUI.url_text.setText(YukiData.playing_url)
            YukiGUI.url_text.setCursorPosition(0)
            if YukiGUI.streaminfo_win.isVisible():
                YukiGUI.streaminfo_win.hide()

        YukiGUI.streaminfo_win.setCentralWidget(YukiGUI.streaminfo_win_widget)

        def show_license():
            if not YukiGUI.license_win.isVisible():
                move_window_to_center(YukiGUI.license_win)
                YukiGUI.license_win.show()
            else:
                YukiGUI.license_win.hide()

        YukiGUI.licensebox_close_btn.clicked.connect(YukiGUI.license_win.close)
        YukiGUI.license_win.setCentralWidget(YukiGUI.licensewin_widget)

        def aboutqt_show():
            QtWidgets.QMessageBox.aboutQt(YukiGUI.help_win, "yuki-iptv")
            YukiGUI.help_win.raise_()
            YukiGUI.help_win.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
            YukiGUI.help_win.activateWindow()

        YukiGUI.license_btn.clicked.connect(show_license)
        YukiGUI.aboutqt_btn.clicked.connect(aboutqt_show)
        YukiGUI.close_btn.clicked.connect(YukiGUI.help_win.close)

        YukiGUI.help_win.setCentralWidget(YukiGUI.helpwin_widget)

        def shortcuts_table_clicked(row1, column1):
            if column1 == 1:  # keybind
                sc1_text = YukiGUI.shortcuts_table.item(row1, column1).text()
                YukiGUI.keyseq.setKeySequence(sc1_text)
                YukiData.selected_shortcut_row = row1
                YukiGUI.keyseq.setFocus()
                move_window_to_center(YukiGUI.shortcuts_win_2)
                YukiGUI.shortcuts_win_2.show()

        YukiGUI.shortcuts_table.cellDoubleClicked.connect(shortcuts_table_clicked)

        def get_widget_item(widget_str):
            twi = QtWidgets.QTableWidgetItem(widget_str)
            twi.setFlags(twi.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            return twi

        def show_shortcuts():
            if not YukiGUI.shortcuts_win.isVisible():
                YukiGUI.shortcuts_table.setRowCount(len(YukiData.main_keybinds))
                keybind_i = -1
                for keybind in YukiData.main_keybinds:
                    keybind_i += 1
                    YukiGUI.shortcuts_table.setItem(
                        keybind_i,
                        0,
                        get_widget_item(main_keybinds_translations[keybind]),
                    )
                    if isinstance(YukiData.main_keybinds[keybind], str):
                        keybind_str = YukiData.main_keybinds[keybind]
                    else:
                        keybind_str = QtGui.QKeySequence(
                            YukiData.main_keybinds[keybind]
                        ).toString()
                    kbd_widget = get_widget_item(keybind_str)
                    kbd_widget.setToolTip(_("Double click to change"))
                    YukiGUI.shortcuts_table.setItem(keybind_i, 1, kbd_widget)
                YukiGUI.shortcuts_table.resizeColumnsToContents()
                move_window_to_center(YukiGUI.shortcuts_win)
                YukiGUI.shortcuts_win.show()
            else:
                YukiGUI.shortcuts_win.hide()

        def show_settings():
            if not YukiGUI.settings_win.isVisible():
                move_window_to_center(YukiGUI.settings_win)
                YukiGUI.settings_win.show()
            else:
                YukiGUI.settings_win.hide()

        YukiData.show_settings = show_settings

        def show_help():
            if not YukiGUI.help_win.isVisible():
                move_window_to_center(YukiGUI.help_win)
                YukiGUI.help_win.show()
            else:
                YukiGUI.help_win.hide()

        def show_sort():
            if not YukiGUI.sort_win.isVisible():
                YukiGUI.sort_list.clear()
                for sort_label_ch in (
                    YukiData.array_sorted
                    if not YukiData.channel_sort
                    else YukiData.channel_sort
                ):
                    YukiGUI.sort_list.addItem(sort_label_ch)

                move_window_to_center(YukiGUI.sort_win)
                YukiGUI.sort_win.show()
            else:
                YukiGUI.sort_win.hide()

        def reload_playlist():
            logger.info("Reloading playlist...")
            save_settings()

        def set_mpv_osc(osc_value):
            if osc_value != YukiData.osc:
                YukiData.osc = osc_value
                YukiData.player.osc = osc_value

        def init_mpv_player():
            YukiData.player = mpv.MPV(
                **options,
                log_handler=my_log,
            )
            YukiData.force_turnoff_osc = not YukiData.player.osc

            logger.info(f"{YukiData.player.mpv_version}")

            YukiGUI.textbox.setText(get_about_text())

            if YukiData.settings["cache_secs"] != 0:
                YukiData.player.demuxer_readahead_secs = YukiData.settings["cache_secs"]
                YukiData.player.cache_secs = YukiData.settings["cache_secs"]
                logger.info(f"Cache set to {YukiData.player.cache_secs}s")
            else:
                logger.info("Using default cache settings")
            YukiData.player.user_agent = default_user_agent
            _referer = (
                YukiData.settings["playlist_referer"]
                if YukiData.settings["playlist_referer"]
                else YukiData.settings["referer"]
            )
            if _referer:
                referer = _referer
                originURL = ""
                if referer.endswith("/"):
                    originURL = referer[:-1]
                if originURL:
                    YukiData.player.http_header_fields = (
                        f"Referer: {referer},Origin: {originURL}"
                    )
                else:
                    YukiData.player.http_header_fields = f"Referer: {referer}"
                logger.info(f"HTTP referer: '{referer}'")
            else:
                logger.info("No HTTP referer set up")
            mpv_override_volume(100)
            YukiData.player.loop = True

            try:
                populate_menubar(
                    0,
                    win.menu_bar_qt,
                    win,
                    YukiData.player.track_list,
                    YukiData.playing_channel,
                    get_keybind,
                )
                populate_menubar(
                    1,
                    YukiData.right_click_menu,
                    win,
                    YukiData.player.track_list,
                    YukiData.playing_channel,
                    get_keybind,
                )
            except Exception:
                logger.warning("populate_menubar failed")
                show_exception(traceback.format_exc(), "populate_menubar failed")
            redraw_menubar()

            @YukiData.player.property_observer("duration")
            def duration_observer(_name, value):
                try:
                    if YukiData.old_playing_url != YukiData.playing_url:
                        YukiData.old_playing_url = YukiData.playing_url
                        YukiData.event_handler.on_metadata()
                except Exception:
                    pass

            @YukiData.player.property_observer("current-vo")
            def vo_observer(_name, value):
                try:
                    if value.strip() == "sdl" and not (
                        "vo" in options_custom
                        and str(options_custom["vo"]).strip() == "sdl"
                    ):
                        logger.info("sdl video output detected, switching to x11")
                        YukiData.player.vo = "x11"
                except Exception:
                    pass

            def seek_event_callback():
                if (
                    YukiData.player
                    and YukiData.mpris_ready
                    and YukiData.mpris_running
                    and not YukiData.stopped
                ):
                    (
                        playback_status,
                        mpris_trackid,
                        artUrl,
                        player_position,
                    ) = get_mpris_metadata()
                    mpris_seeked(player_position)

            @YukiData.player.event_callback("seek")
            def seek_event(event):
                execute_in_main_thread(partial(seek_event_callback))

            @YukiData.player.event_callback("file-loaded")
            def file_loaded_2(event):
                execute_in_main_thread(partial(file_loaded_callback))

            @YukiData.player.event_callback("end_file")
            def ready_handler_2(event):
                _event = event.as_dict()
                if "reason" in _event and "error" in decode(_event["reason"]):
                    execute_in_main_thread(partial(end_file_error_callback))
                else:
                    execute_in_main_thread(partial(end_file_callback))

            @YukiData.player.on_key_press("MBTN_RIGHT")
            def my_mouse_right():
                execute_in_main_thread(partial(my_mouse_right_callback))

            @YukiData.player.on_key_press("MBTN_LEFT")
            def my_mouse_left():
                execute_in_main_thread(partial(my_mouse_left_callback))

            @YukiData.player.on_key_press("MBTN_LEFT_DBL")
            def my_leftdbl_binding():
                mpv_fullscreen()

            @YukiData.player.on_key_press("MBTN_FORWARD")
            def my_forward_binding():
                next_channel()

            @YukiData.player.on_key_press("MBTN_BACK")
            def my_back_binding():
                prev_channel()

            @YukiData.player.on_key_press("WHEEL_UP")
            def my_up_binding():
                my_up_binding_execute()

            @YukiData.player.on_key_press("WHEEL_DOWN")
            def my_down_binding():
                my_down_binding_execute()

            def pause_handler():
                try:
                    if not YukiData.player.pause:
                        YukiGUI.btn_playpause.setIcon(
                            QtGui.QIcon(str(Path(YukiGUI.icons_folder, "pause.png")))
                        )
                        YukiGUI.btn_playpause.setToolTip(_("Pause"))
                    else:
                        YukiGUI.btn_playpause.setIcon(
                            QtGui.QIcon(str(Path(YukiGUI.icons_folder, "play.png")))
                        )
                        YukiGUI.btn_playpause.setToolTip(_("Play"))
                    if YukiData.event_handler:
                        try:
                            YukiData.event_handler.on_playpause()
                        except Exception:
                            pass
                except Exception:
                    pass

            def async_pause_handler(*args, **kwargs):
                execute_in_main_thread(partial(pause_handler))

            YukiData.player.observe_property("pause", async_pause_handler)

            def yuki_track_set(track, type1):
                logger.info(f"Set {type1} track to {track}")
                if YukiData.playing_channel not in YukiData.player_tracks:
                    YukiData.player_tracks[YukiData.playing_channel] = {}
                if type1 == "vid":
                    YukiData.player.vid = track
                    YukiData.player_tracks[YukiData.playing_channel]["vid"] = track
                elif type1 == "aid":
                    YukiData.player.aid = track
                    YukiData.player_tracks[YukiData.playing_channel]["aid"] = track
                elif type1 == "sid":
                    YukiData.player.sid = track
                    YukiData.player_tracks[YukiData.playing_channel]["sid"] = track

            init_menubar_player(
                YukiData.player,
                mpv_play,
                mpv_stop,
                prev_channel,
                next_channel,
                mpv_fullscreen,
                showhideeverything,
                main_channel_settings,
                show_settings,
                show_help,
                do_screenshot,
                mpv_mute,
                showhideplaylist,
                lowpanel_ch_1,
                open_stream_info,
                app.quit,
                redraw_menubar,
                QtGui.QIcon(
                    QtGui.QIcon(str(Path(YukiGUI.icons_folder, "circle.png"))).pixmap(
                        8, 8
                    )
                ),
                my_up_binding_execute,
                my_down_binding_execute,
                show_playlist_editor,
                show_playlists,
                show_sort,
                show_exception,
                force_update_epg_act,
                get_keybind,
                show_tvguide_2,
                show_multi_epg,
                reload_playlist,
                show_shortcuts,
                yuki_track_set,
                mpv_frame_step,
                mpv_frame_back_step,
            )

            volume_option1 = read_option("volume")
            if volume_option1 is not None:
                logger.info(f"Set volume to {vol_remembered}")
                YukiGUI.volume_slider.setValue(vol_remembered)
                mpv_volume_set()
            else:
                YukiGUI.volume_slider.setValue(100)
                mpv_volume_set()

        def set_label_width(label, width):
            if width > 0:
                label.setFixedWidth(width)

        class MainWindow(QtWidgets.QMainWindow):
            oldpos = None
            oldpos1 = None

            def __init__(self, parent=None):
                super().__init__(parent)
                self.windowWidth = self.width()
                self.windowHeight = self.height()
                self.container = None
                self.listWidget = None
                self.moviesWidget = None
                self.seriesWidget = None
                self.createMenuBar_mw()

                class Container(QtWidgets.QWidget):
                    def mousePressEvent(self, event3):
                        if event3.button() == QtCore.Qt.MouseButton.LeftButton:
                            execute_in_main_thread(partial(my_mouse_left_callback))
                        elif event3.button() == QtCore.Qt.MouseButton.RightButton:
                            execute_in_main_thread(partial(my_mouse_right_callback))
                        elif event3.button() in [
                            QtCore.Qt.MouseButton.BackButton,
                            QtCore.Qt.MouseButton.XButton1,
                            QtCore.Qt.MouseButton.ExtraButton1,
                        ]:
                            prev_channel()
                        elif event3.button() in [
                            QtCore.Qt.MouseButton.ForwardButton,
                            QtCore.Qt.MouseButton.XButton2,
                            QtCore.Qt.MouseButton.ExtraButton2,
                        ]:
                            next_channel()
                        else:
                            super().mousePressEvent(event3)

                    def mouseDoubleClickEvent(self, event3):
                        if event3.button() == QtCore.Qt.MouseButton.LeftButton:
                            mpv_fullscreen()

                    def wheelEvent(self, event3):
                        if event3.angleDelta().y() > 0:
                            my_up_binding_execute()
                        else:
                            my_down_binding_execute()
                        event3.accept()

                self.container = QtWidgets.QWidget(self)
                self.setCentralWidget(self.container)
                self.container.setAttribute(
                    QtCore.Qt.WidgetAttribute.WA_DontCreateNativeAncestors
                )
                self.container.setAttribute(QtCore.Qt.WidgetAttribute.WA_NativeWindow)
                self.container.setFocus()
                self.container.setStyleSheet(
                    """
                    background-color: #C0C6CA;
                """
                )

            def resize_rewind(self):
                rewind_normal_offset = 150
                rewind_fullscreen_offset = 180
                if YukiData.settings["panelposition"] == 2:
                    dockWidget_playlist_cur_width = 0
                else:
                    dockWidget_playlist_cur_width = dockWidget_playlist.width()

                if not YukiData.fullscreen:
                    if not dockWidget_controlPanel.isVisible():
                        set_label_width(
                            YukiGUI.rewind,
                            self.windowWidth - dockWidget_playlist_cur_width + 58,
                        )
                        YukiGUI.rewind.move(
                            int(
                                ((self.windowWidth - YukiGUI.rewind.width()) / 2)
                                - (dockWidget_playlist_cur_width / 1.7)
                            ),
                            int(
                                (self.windowHeight - YukiGUI.rewind.height())
                                - rewind_fullscreen_offset
                            ),
                        )
                    else:
                        set_label_width(
                            YukiGUI.rewind,
                            self.windowWidth - dockWidget_playlist_cur_width + 58,
                        )
                        YukiGUI.rewind.move(
                            int(
                                ((self.windowWidth - YukiGUI.rewind.width()) / 2)
                                - (dockWidget_playlist_cur_width / 1.7)
                            ),
                            int(
                                (self.windowHeight - YukiGUI.rewind.height())
                                - dockWidget_controlPanel.height()
                                - rewind_normal_offset
                            ),
                        )
                else:
                    set_label_width(YukiGUI.rewind, YukiGUI.controlpanel_widget.width())
                    rewind_position_x = (
                        YukiGUI.controlpanel_widget.pos().x() - win.pos().x()
                    )
                    if rewind_position_x < 0:
                        rewind_position_x = 0
                    YukiGUI.rewind.move(
                        rewind_position_x,
                        int(
                            (self.windowHeight - YukiGUI.rewind.height())
                            - rewind_fullscreen_offset
                        ),
                    )

            def update(self):
                if YukiData.settings["panelposition"] == 2:
                    dockWidget_playlist_cur_width2 = 0
                else:
                    dockWidget_playlist_cur_width2 = dockWidget_playlist.width()

                self.windowWidth = self.width()
                self.windowHeight = self.height()
                if YukiData.settings["panelposition"] in (0, 2):
                    YukiData.tvguide_lbl.move(2, YukiGUI.tvguide_lbl_offset)
                else:
                    YukiData.tvguide_lbl.move(
                        win.width() - YukiData.tvguide_lbl.width(),
                        YukiGUI.tvguide_lbl_offset,
                    )
                self.resize_rewind()
                if not YukiData.fullscreen:
                    if not dockWidget_controlPanel.isVisible():
                        set_label_width(
                            YukiData.state,
                            self.windowWidth - dockWidget_playlist_cur_width2 + 58,
                        )
                        YukiData.state.move(
                            int(
                                ((self.windowWidth - YukiData.state.width()) / 2)
                                - (dockWidget_playlist_cur_width2 / 1.7)
                            ),
                            int((self.windowHeight - YukiData.state.height()) - 20),
                        )
                        h = 0
                        h2 = 10
                    else:
                        set_label_width(
                            YukiData.state,
                            self.windowWidth - dockWidget_playlist_cur_width2 + 58,
                        )
                        YukiData.state.move(
                            int(
                                ((self.windowWidth - YukiData.state.width()) / 2)
                                - (dockWidget_playlist_cur_width2 / 1.7)
                            ),
                            int(
                                (self.windowHeight - YukiData.state.height())
                                - dockWidget_controlPanel.height()
                                - 10
                            ),
                        )
                        h = dockWidget_controlPanel.height()
                        h2 = 20
                else:
                    set_label_width(YukiData.state, self.windowWidth)
                    YukiData.state.move(
                        int((self.windowWidth - YukiData.state.width()) / 2),
                        int((self.windowHeight - YukiData.state.height()) - 20),
                    )
                    h = 0
                    h2 = 10
                if dockWidget_playlist.isVisible():
                    if YukiData.settings["panelposition"] in (0, 2):
                        YukiGUI.lbl2.move(0, YukiGUI.lbl2_offset)
                    else:
                        YukiGUI.lbl2.move(
                            YukiData.tvguide_lbl.width() + YukiGUI.lbl2.width(),
                            YukiGUI.lbl2_offset,
                        )
                else:
                    YukiGUI.lbl2.move(0, YukiGUI.lbl2_offset)
                if YukiData.state.isVisible():
                    state_h = YukiData.state.height()
                else:
                    state_h = 15
                YukiData.tvguide_lbl.setFixedHeight(
                    (self.windowHeight - state_h - h) - 40 - state_h + h2
                )

            def resizeEvent(self, event):
                try:
                    self.update()
                except Exception:
                    pass
                QtWidgets.QMainWindow.resizeEvent(self, event)

            def closeEvent(self, event1):
                try:
                    YukiData.player.vo = "null"
                except Exception:
                    pass
                if YukiGUI.streaminfo_win.isVisible():
                    YukiGUI.streaminfo_win.hide()
                if YukiData.settings["panelposition"] == 2:
                    dockWidget_playlist.hide()

            def createMenuBar_mw(self):
                self.menu_bar_qt = self.menuBar()
                init_yuki_iptv_menubar(self, app, self.menu_bar_qt)

        win = MainWindow()
        win.setMinimumSize(1, 1)
        win.setWindowTitle("yuki-iptv")
        win.setWindowIcon(YukiGUI.main_icon)
        YukiGUI.win = win

        YukiGUI.create3()

        window_data = read_option("window")
        if window_data:
            win.setGeometry(
                window_data["x"], window_data["y"], window_data["w"], window_data["h"]
            )
        else:
            YukiData.needs_resize = True
            win.resize(WINDOW_SIZE[0], WINDOW_SIZE[1])
            move_window_to_center(win)

        def get_curwindow_pos():
            try:
                win_geometry = win.screen().availableGeometry()
            except Exception:
                win_geometry = QtWidgets.QDesktopWidget().screenGeometry(win)
            win_width = win_geometry.width()
            win_height = win_geometry.height()
            logger.debug(f"Screen size: {win_width}x{win_height}")
            return (
                win_width,
                win_height,
            )

        def showLoading2():
            if not YukiGUI.loading2.isVisible():
                YukiGUI.centerwidget(YukiGUI.loading2, 50)
                YukiGUI.loading_movie2.stop()
                YukiGUI.loading_movie2.start()
                YukiGUI.loading2.show()

        def hideLoading2():
            if YukiGUI.loading2.isVisible():
                YukiGUI.loading2.hide()
                YukiGUI.loading_movie2.stop()

        def show_progress(prog):
            if not YukiData.settings["hidetvprogram"] and (
                prog and not YukiData.playing_archive
            ):
                prog_percentage = round(
                    (time.time() - prog["start"])
                    / (prog["stop"] - prog["start"])
                    * 100,
                    2,
                )
                prog_title = prog["title"]
                prog_start = prog["start"]
                prog_stop = prog["stop"]
                prog_start_time = datetime.datetime.fromtimestamp(prog_start).strftime(
                    "%H:%M"
                )
                prog_stop_time = datetime.datetime.fromtimestamp(prog_stop).strftime(
                    "%H:%M"
                )
                YukiGUI.progress.setValue(int(prog_percentage))
                YukiGUI.progress.setFormat(str(prog_percentage) + "% " + prog_title)
                YukiGUI.progress.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
                YukiGUI.start_label.setText(prog_start_time)
                YukiGUI.stop_label.setText(prog_stop_time)
                if not YukiData.fullscreen:
                    YukiGUI.progress.show()
                    YukiGUI.start_label.show()
                    YukiGUI.stop_label.show()
            else:
                YukiGUI.progress.hide()
                YukiGUI.start_label.setText("")
                YukiGUI.start_label.hide()
                YukiGUI.stop_label.setText("")
                YukiGUI.stop_label.hide()

        def set_mpv_title():
            try:
                YukiData.player.title = win.windowTitle()
            except Exception:
                pass

        def setChannelText(channelText, do_channel_set=False):
            chTextStrip = channelText.strip()
            if chTextStrip:
                win.setWindowTitle(f"{chTextStrip} - yuki-iptv")
            else:
                win.setWindowTitle("yuki-iptv")
            execute_in_main_thread(partial(set_mpv_title))
            if not do_channel_set:
                YukiGUI.channel.setText(f"{chr(9654)} {channelText}")
                YukiGUI.channel.show()
            if (
                YukiData.fullscreen
                and chTextStrip
                and not YukiData.dockWidget_playlistVisible
            ):
                YukiData.state.show()
                YukiData.state.setTextYuki(chTextStrip)
                YukiData.time_stop = time.time() + 1

        def idle_on_metadata():
            try:
                YukiData.event_handler.on_metadata()
            except Exception:
                pass

        def set_player_settings(j):
            try:
                logger.info("Waiting for channel load...")
                try:
                    YukiData.player.wait_until_playing()
                except Exception:
                    pass
                if j == YukiData.playing_channel:
                    logger.info(f"Setting player settings for channel: {j}")
                    execute_in_main_thread(partial(idle_on_metadata))
                    if (
                        YukiData.settings["m3u"] in YukiData.channel_sets
                        and j in YukiData.channel_sets[YukiData.settings["m3u"]]
                    ):
                        d = YukiData.channel_sets[YukiData.settings["m3u"]][j]
                        YukiData.player.deinterlace = d["deinterlace"]
                        if "ua" not in d:
                            d["ua"] = ""
                        if "ref" not in d:
                            d["ref"] = ""
                        if "contrast" in d:
                            YukiData.player.contrast = d["contrast"]
                        else:
                            YukiData.player.contrast = 0
                        if "brightness" in d:
                            YukiData.player.brightness = d["brightness"]
                        else:
                            YukiData.player.brightness = 0
                        if "hue" in d:
                            YukiData.player.hue = d["hue"]
                        else:
                            YukiData.player.hue = 0
                        if "saturation" in d:
                            YukiData.player.saturation = d["saturation"]
                        else:
                            YukiData.player.saturation = 0
                        if "gamma" in d:
                            YukiData.player.gamma = d["gamma"]
                        else:
                            YukiData.player.gamma = 0
                        if "videoaspect" in d:
                            setVideoAspect(
                                YukiGUI.videoaspect_vars[
                                    list(YukiGUI.videoaspect_vars)[d["videoaspect"]]
                                ]
                            )
                        else:
                            setVideoAspect(
                                YukiGUI.videoaspect_vars[
                                    YukiGUI.videoaspect_def_choose.itemText(
                                        YukiData.settings["videoaspect"]
                                    )
                                ]
                            )
                        if "zoom" in d:
                            YukiData.player.video_zoom = YukiGUI.zoom_vars[
                                list(YukiGUI.zoom_vars)[d["zoom"]]
                            ]
                        else:
                            YukiData.player.video_zoom = YukiGUI.zoom_vars[
                                YukiGUI.zoom_def_choose.itemText(
                                    YukiData.settings["zoom"]
                                )
                            ]
                        if "panscan" in d:
                            YukiData.player.panscan = d["panscan"]
                        else:
                            YukiData.player.panscan = YukiData.settings["panscan"]
                    else:
                        YukiData.player.deinterlace = YukiData.settings["deinterlace"]
                        setVideoAspect(
                            YukiGUI.videoaspect_vars[
                                YukiGUI.videoaspect_def_choose.itemText(
                                    YukiData.settings["videoaspect"]
                                )
                            ]
                        )
                        YukiData.player.video_zoom = YukiGUI.zoom_vars[
                            YukiGUI.zoom_def_choose.itemText(YukiData.settings["zoom"])
                        ]
                        YukiData.player.panscan = YukiData.settings["panscan"]
                        YukiData.player.gamma = 0
                        YukiData.player.saturation = 0
                        YukiData.player.hue = 0
                        YukiData.player.brightness = 0
                        YukiData.player.contrast = 0
                    if YukiData.player.deinterlace:
                        logger.info("Deinterlace: enabled")
                    else:
                        logger.info("Deinterlace: disabled")
                    logger.info(f"Contrast: {YukiData.player.contrast}")
                    logger.info(f"Brightness: {YukiData.player.brightness}")
                    logger.info(f"Hue: {YukiData.player.hue}")
                    logger.info(f"Saturation: {YukiData.player.saturation}")
                    logger.info(f"Gamma: {YukiData.player.gamma}")
                    logger.info(f"Video aspect: {getVideoAspect()}")
                    logger.info(f"Zoom: {YukiData.player.video_zoom}")
                    logger.info(f"Panscan: {YukiData.player.panscan}")

                    if YukiData.playing_channel in YukiData.player_tracks:
                        last_track = YukiData.player_tracks[YukiData.playing_channel]
                        if "vid" in last_track:
                            logger.info(
                                f"Restoring last video track: '{last_track['vid']}'"
                            )
                            YukiData.player.vid = last_track["vid"]
                        else:
                            YukiData.player.vid = "auto"
                        if "aid" in last_track:
                            logger.info(
                                f"Restoring last audio track: '{last_track['aid']}'"
                            )
                            YukiData.player.aid = last_track["aid"]
                        else:
                            YukiData.player.aid = "auto"
                        if "sid" in last_track:
                            logger.info(
                                f"Restoring last sub track: '{last_track['sid']}'"
                            )
                            YukiData.player.sid = last_track["sid"]
                        else:
                            YukiData.player.sid = "auto"
                    else:
                        YukiData.player.vid = "auto"
                        YukiData.player.aid = "auto"
                        YukiData.player.sid = "auto"
                    execute_in_main_thread(partial(file_loaded_callback))
            except Exception:
                pass

        def itemClicked_event(item, custom_url="", archived=False, is_rewind=False):
            is_ic_ok = True
            try:
                is_ic_ok = item.text() != _("Nothing found")
            except Exception:
                pass
            if is_ic_ok:
                YukiData.playing_archive = archived
                if not archived:
                    YukiData.archive_epg = None
                    YukiGUI.rewind_slider.setValue(100)
                    YukiData.rewind_value = YukiGUI.rewind_slider.value()
                else:
                    if not is_rewind:
                        YukiGUI.rewind_slider.setValue(0)
                        YukiData.rewind_value = YukiGUI.rewind_slider.value()
                try:
                    j = item.data(QtCore.Qt.ItemDataRole.UserRole)
                except Exception:
                    j = item
                if not j:
                    return
                YukiData.playing_channel = j
                YukiData.playing_group = playmode_selector.currentIndex()
                YukiData.item_selected = j
                array_item = None
                try:
                    array_item = getArrayItem(j)
                    play_url = array_item["url"]
                except Exception:
                    play_url = custom_url
                if archived:
                    play_url = custom_url
                MAX_CHAN_SIZE = 35
                channel_name = j
                if len(channel_name) > MAX_CHAN_SIZE:
                    channel_name = channel_name[: MAX_CHAN_SIZE - 3] + "..."
                setChannelText("  " + channel_name)
                current_prog = None
                if get_epg_url() and array_item:
                    epg_id = get_epg_id(array_item)
                    if epg_id:
                        programme = get_current_programme(epg_id)
                        if programme:
                            current_prog = programme
                YukiData.current_prog1 = current_prog
                show_progress(current_prog)
                if YukiGUI.start_label.isVisible():
                    dockWidget_controlPanel.setFixedHeight(
                        DOCKWIDGET_CONTROLPANEL_HEIGHT_HIGH
                    )
                else:
                    dockWidget_controlPanel.setFixedHeight(
                        DOCKWIDGET_CONTROLPANEL_HEIGHT_LOW
                    )
                inhibit()
                YukiData.playing = True
                win.update()
                YukiData.playing_url = play_url
                execute_in_main_thread(partial(set_url_text))
                ua_choose = default_user_agent
                if (
                    YukiData.settings["m3u"] in YukiData.channel_sets
                    and j in YukiData.channel_sets[YukiData.settings["m3u"]]
                ):
                    ua_choose = YukiData.channel_sets[YukiData.settings["m3u"]][j]["ua"]
                if not custom_url:
                    doPlay(play_url, ua_choose, j)
                else:
                    doPlay(custom_url, ua_choose, j)
                execute_in_main_thread(partial(redraw_channels))

        def itemSelected_event(item):
            try:
                n_1 = item.data(QtCore.Qt.ItemDataRole.UserRole)
                YukiData.item_selected = n_1
                update_tvguide(n_1)
            except Exception:
                pass

        def mpv_play():
            YukiData.player.pause = not YukiData.player.pause

        def mpv_stop():
            YukiData.playing_channel = ""
            YukiData.playing_group = -1
            YukiData.playing_url = ""
            execute_in_main_thread(partial(set_url_text))
            hideLoading()
            setChannelText("")
            uninhibit()
            YukiData.playing = False
            stopPlayer()
            YukiData.player.loop = True
            YukiData.player.deinterlace = False
            mpv_override_play(str(Path(YukiGUI.icons_folder, "main.png")))
            YukiData.player.pause = True
            YukiGUI.channel.setText("")
            YukiGUI.channel.hide()
            YukiGUI.progress.hide()
            YukiGUI.start_label.hide()
            YukiGUI.stop_label.hide()
            YukiGUI.start_label.setText("")
            YukiGUI.stop_label.setText("")
            dockWidget_controlPanel.setFixedHeight(DOCKWIDGET_CONTROLPANEL_HEIGHT_LOW)
            win.update()
            execute_in_main_thread(partial(redraw_channels))
            redraw_menubar()

        def esc_handler():
            if YukiData.fullscreen:
                mpv_fullscreen()

        YukiData.currentWidthHeight = [
            win.geometry().x(),
            win.geometry().y(),
            win.width(),
            win.height(),
        ]
        YukiData.currentMaximized = win.isMaximized()

        def idle_mpv_fullscreen():
            if not YukiData.fullscreen:
                # Entering fullscreen
                if not YukiData.fullscreen_locked:
                    YukiData.fullscreen_locked = True
                    rewind_layout_offset = 10
                    YukiGUI.rewind_layout.setContentsMargins(
                        rewind_layout_offset, 0, rewind_layout_offset - 50, 0
                    )
                    YukiData.isControlPanelVisible = dockWidget_controlPanel.isVisible()
                    YukiData.isPlaylistVisible = dockWidget_playlist.isVisible()
                    setShortcutState(True)
                    YukiData.currentWidthHeight = [
                        win.geometry().x(),
                        win.geometry().y(),
                        win.width(),
                        win.height(),
                    ]
                    YukiData.currentMaximized = win.isMaximized()
                    YukiGUI.channelfilter.usePopup = False
                    win.menu_bar_qt.hide()
                    YukiData.fullscreen = True
                    dockWidget_playlist.hide()
                    YukiGUI.label_video_data.hide()
                    YukiGUI.label_avsync.hide()
                    for lbl3 in YukiGUI.controlpanel_btns:
                        if lbl3 not in YukiGUI.show_lbls_fullscreen:
                            lbl3.hide()
                    YukiGUI.progress.hide()
                    YukiGUI.start_label.hide()
                    YukiGUI.stop_label.hide()
                    dockWidget_controlPanel.hide()
                    dockWidget_controlPanel.setFixedHeight(
                        DOCKWIDGET_CONTROLPANEL_HEIGHT_LOW
                    )
                    win.update()
                    win.raise_()
                    win.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
                    win.activateWindow()
                    win.showFullScreen()
                    if YukiData.settings["panelposition"] == 1:
                        tvguide_close_lbl.move(
                            get_curwindow_pos()[0] - YukiData.tvguide_lbl.width() - 40,
                            YukiGUI.tvguide_lbl_offset,
                        )
                    YukiGUI.centerwidget(YukiGUI.loading1)
                    YukiGUI.centerwidget(YukiGUI.loading2, 50)
                    YukiData.fullscreen_locked = False
            else:
                # Leaving fullscreen
                if not YukiData.fullscreen_locked:
                    YukiData.fullscreen_locked = True
                    YukiGUI.rewind_layout.setContentsMargins(100, 0, 50, 0)
                    setShortcutState(False)
                    if YukiData.state.isVisible() and YukiData.state.text().startswith(
                        _("Volume")
                    ):
                        YukiData.state.hide()
                    win.menu_bar_qt.show()
                    hide_playlist_fullscreen()
                    hide_controlpanel_fullscreen()
                    dockWidget_playlist.setWindowOpacity(1)
                    dockWidget_playlist.hide()
                    dockWidget_controlPanel.setWindowOpacity(1)
                    dockWidget_controlPanel.hide()
                    YukiData.fullscreen = False
                    if YukiData.state.text().endswith(
                        "{} F".format(_("To exit fullscreen mode press"))
                    ):
                        YukiData.state.setTextYuki("")
                        if not YukiData.gl_is_static:
                            YukiData.state.hide()
                            win.update()
                    if (
                        not YukiData.player.pause
                        and YukiData.playing
                        and YukiGUI.start_label.text()
                    ):
                        YukiGUI.progress.show()
                        YukiGUI.start_label.show()
                        YukiGUI.stop_label.show()
                        dockWidget_controlPanel.setFixedHeight(
                            DOCKWIDGET_CONTROLPANEL_HEIGHT_HIGH
                        )
                    YukiGUI.label_video_data.show()
                    YukiGUI.label_avsync.show()
                    for lbl3 in YukiGUI.controlpanel_btns:
                        if lbl3 not in YukiGUI.show_lbls_fullscreen:
                            lbl3.show()
                    dockWidget_controlPanel.show()
                    dockWidget_playlist.show()
                    win.update()
                    if not YukiData.currentMaximized:
                        win.showNormal()
                    else:
                        win.showMaximized()
                    win.setGeometry(
                        YukiData.currentWidthHeight[0],
                        YukiData.currentWidthHeight[1],
                        YukiData.currentWidthHeight[2],
                        YukiData.currentWidthHeight[3],
                    )
                    if not YukiData.isPlaylistVisible:
                        show_hide_playlist()
                    if YukiData.settings["panelposition"] == 1:
                        tvguide_close_lbl.move(
                            win.width() - YukiData.tvguide_lbl.width() - 40,
                            YukiGUI.tvguide_lbl_offset,
                        )
                    YukiGUI.centerwidget(YukiGUI.loading1)
                    YukiGUI.centerwidget(YukiGUI.loading2, 50)
                    if YukiData.isControlPanelVisible:
                        dockWidget_controlPanel.show()
                    else:
                        dockWidget_controlPanel.hide()
                    if YukiData.compact_mode:
                        win.menu_bar_qt.hide()
                        setShortcutState(True)
                    dockWidget_playlist.lower()
                    YukiData.fullscreen_locked = False
            try:
                YukiData.event_handler.on_fullscreen()
            except Exception:
                pass

        def mpv_fullscreen():
            execute_in_main_thread(partial(idle_mpv_fullscreen))

        def is_show_volume():
            showdata = YukiData.fullscreen
            if not YukiData.fullscreen and win.isVisible():
                showdata = not dockWidget_controlPanel.isVisible()
            return showdata and not YukiGUI.controlpanel_widget.isVisible()

        def show_volume(v1):
            if is_show_volume():
                YukiData.state.show()
                if isinstance(v1, str):
                    YukiData.state.setTextYuki(v1)
                else:
                    YukiData.state.setTextYuki("{}: {}%".format(_("Volume"), int(v1)))

        def mpv_mute():
            YukiData.time_stop = time.time() + 3
            if YukiData.player.mute:
                if YukiData.old_value > 50:
                    YukiGUI.btn_volume.setIcon(
                        QtGui.QIcon(str(Path(YukiGUI.icons_folder, "volume.png")))
                    )
                else:
                    YukiGUI.btn_volume.setIcon(
                        QtGui.QIcon(str(Path(YukiGUI.icons_folder, "volume-low.png")))
                    )
                mpv_override_mute(False)
                YukiGUI.volume_slider.setValue(YukiData.old_value)
                show_volume(YukiData.old_value)
            else:
                YukiGUI.btn_volume.setIcon(
                    QtGui.QIcon(str(Path(YukiGUI.icons_folder, "mute.png")))
                )
                mpv_override_mute(True)
                YukiData.old_value = YukiGUI.volume_slider.value()
                YukiGUI.volume_slider.setValue(0)
                show_volume(_("Volume off"))

        def mpv_volume_set():
            YukiData.time_stop = time.time() + 3
            vol = int(YukiGUI.volume_slider.value())
            try:
                if vol == 0:
                    show_volume(_("Volume off"))
                else:
                    show_volume(vol)
            except NameError:
                pass
            mpv_override_volume(vol)
            if vol == 0:
                mpv_override_mute(True)
                YukiGUI.btn_volume.setIcon(
                    QtGui.QIcon(str(Path(YukiGUI.icons_folder, "mute.png")))
                )
            else:
                mpv_override_mute(False)
                if vol > 50:
                    YukiGUI.btn_volume.setIcon(
                        QtGui.QIcon(str(Path(YukiGUI.icons_folder, "volume.png")))
                    )
                else:
                    YukiGUI.btn_volume.setIcon(
                        QtGui.QIcon(str(Path(YukiGUI.icons_folder, "volume-low.png")))
                    )

        class PlaylistDockWidget(QtWidgets.QDockWidget):
            def enterEvent(self, event4):
                YukiData.check_playlist_visible = True

            def leaveEvent(self, event4):
                YukiData.check_playlist_visible = False

        dockWidget_playlist = PlaylistDockWidget(win)

        win.listWidget = QtWidgets.QListWidget()
        win.moviesWidget = QtWidgets.QListWidget()
        win.seriesWidget = QtWidgets.QListWidget()

        def tvguide_close_lbl_func(*args, **kwargs):
            hide_tvguide()

        YukiData.tvguide_lbl = YukiGUI.ScrollableLabel(win)
        YukiData.tvguide_lbl.move(0, YukiGUI.tvguide_lbl_offset)
        YukiData.tvguide_lbl.setFixedWidth(TVGUIDE_WIDTH)
        YukiData.tvguide_lbl.hide()

        YukiGUI.set_widget_opacity(YukiData.tvguide_lbl, YukiGUI.DEFAULT_OPACITY)

        class ClickableLabel(QtWidgets.QLabel):
            def __init__(self, whenClicked, win, parent=None):
                QtWidgets.QLabel.__init__(self, win)
                self._whenClicked = whenClicked

            def mouseReleaseEvent(self, event):
                self._whenClicked(event)

        tvguide_close_lbl = ClickableLabel(tvguide_close_lbl_func, win)
        tvguide_close_lbl.setPixmap(
            QtGui.QIcon(str(Path(YukiGUI.icons_folder, "close.png"))).pixmap(32, 32)
        )
        tvguide_close_lbl.setStyleSheet(
            "background-color: {};".format(
                "black" if YukiData.use_dark_icon_theme else "white"
            )
        )
        tvguide_close_lbl.resize(32, 32)
        if YukiData.settings["panelposition"] in (0, 2):
            tvguide_close_lbl.move(
                YukiData.tvguide_lbl.width() + 5, YukiGUI.tvguide_lbl_offset
            )
        else:
            tvguide_close_lbl.move(
                win.width() - YukiData.tvguide_lbl.width() - 40,
                YukiGUI.tvguide_lbl_offset,
            )
            YukiGUI.lbl2.move(
                YukiData.tvguide_lbl.width() + YukiGUI.lbl2.width(), YukiGUI.lbl2_offset
            )
        tvguide_close_lbl.hide()

        YukiGUI.set_widget_opacity(tvguide_close_lbl, YukiGUI.DEFAULT_OPACITY)

        YukiData.current_group = _("All channels")

        YukiData.mp_manager_dict["logos_inprogress"] = False
        YukiData.mp_manager_dict["logos_completed"] = False
        YukiData.mp_manager_dict["logosmovie_inprogress"] = False
        YukiData.mp_manager_dict["logosmovie_completed"] = False
        logos_cache = {}

        def get_pixmap_from_filename(pixmap_filename):
            if pixmap_filename in logos_cache:
                return logos_cache[pixmap_filename]
            else:
                try:
                    if os.path.isfile(pixmap_filename):
                        icon_pixmap = QtGui.QIcon(pixmap_filename).pixmap(
                            QtCore.QSize(32, 32)
                        )
                        if icon_pixmap.isNull():
                            raise Exception("icon_pixmap is null")
                        if not icon_pixmap.height():
                            raise Exception("icon_pixmap height is 0")
                        logos_cache[pixmap_filename] = icon_pixmap
                        icon_pixmap = None
                        return logos_cache[pixmap_filename]
                    else:
                        if pixmap_filename:
                            YukiData.broken_logos.add(pixmap_filename)
                        return None
                except Exception:
                    if pixmap_filename:
                        YukiData.broken_logos.add(pixmap_filename)
                    return None

        def timer_logos_update():
            try:
                if not YukiData.timer_logos_update_lock:
                    YukiData.timer_logos_update_lock = True
                    if YukiData.mp_manager_dict["logos_completed"]:
                        YukiData.mp_manager_dict["logos_completed"] = False
                        execute_in_main_thread(partial(redraw_channels))
                    if YukiData.mp_manager_dict["logosmovie_completed"]:
                        YukiData.mp_manager_dict["logosmovie_completed"] = False
                        update_movie_icons()
                    YukiData.timer_logos_update_lock = False
            except Exception:
                pass

        all_channels_lang = _("All channels")
        favourites_lang = _("Favourites")

        def get_page_count(array_len):
            return max(1, math.ceil(array_len / 100))

        max_width = win.listWidget.sizeHint().width()

        def generate_channels():
            channel_logos_request = {}

            try:
                idx = (YukiGUI.page_box.value() - 1) * 100
            except Exception:
                idx = 0

            # Group and favourites filter
            array_filtered = []
            for j1 in YukiData.array_sorted:
                group1 = YukiData.array[j1]["tvg-group"]
                if YukiData.current_group != all_channels_lang:
                    if YukiData.current_group == favourites_lang:
                        if j1 not in YukiData.favourite_sets:
                            continue
                    else:
                        if group1 != YukiData.current_group:
                            continue
                array_filtered.append(j1)

            ch_array = [
                x13
                for x13 in array_filtered
                if YukiData.search.lower().strip() in x13.lower().strip()
            ]
            ch_array = ch_array[idx : idx + 100]
            try:
                if YukiData.search:
                    YukiGUI.page_box.setMaximum(get_page_count(len(ch_array)))
                    YukiGUI.of_lbl.setText(f"/ {get_page_count(len(ch_array))}")
                else:
                    YukiGUI.page_box.setMaximum(get_page_count(len(array_filtered)))
                    YukiGUI.of_lbl.setText(f"/ {get_page_count(len(array_filtered))}")
            except Exception:
                pass
            res = {}
            k0 = -1
            k = 0
            for i in ch_array:
                k0 += 1
                k += 1
                prog = ""
                orig_category = ""
                orig_desc = ""
                prog_desc = ""

                epg_id = get_epg_id(YukiData.array[i])
                epg_found = False

                if epg_id:
                    current_prog = get_current_programme(epg_id)
                    if current_prog and current_prog["start"] != 0:
                        epg_found = True
                        start_time = datetime.datetime.fromtimestamp(
                            current_prog["start"]
                        ).strftime("%H:%M")
                        stop_time = datetime.datetime.fromtimestamp(
                            current_prog["stop"]
                        ).strftime("%H:%M")
                        t_t = time.time()
                        percentage = round(
                            (t_t - current_prog["start"])
                            / (current_prog["stop"] - current_prog["start"])
                            * 100,
                            2,
                        )
                        if YukiData.settings["hideepgpercentage"]:
                            prog = current_prog["title"]
                        else:
                            prog = str(percentage) + "% " + current_prog["title"]
                        try:
                            if current_prog["desc"]:
                                orig_desc = current_prog["desc"]
                                prog_desc = "\n\n" + textwrap.fill(
                                    current_prog["desc"], 100
                                )
                            else:
                                orig_desc = ""
                                prog_desc = ""
                        except Exception:
                            orig_desc = ""
                            prog_desc = ""
                        try:
                            if current_prog["category"]:
                                orig_category = current_prog["category"]
                        except Exception:
                            orig_category = ""
                    else:
                        start_time = ""
                        stop_time = ""
                        t_t = time.time()
                        percentage = 0
                        prog = ""
                        orig_desc = ""
                        prog_desc = ""
                        orig_category = ""
                MyPlaylistWidget = YukiGUI.PlaylistWidget(YukiGUI)
                channel_name = i

                original_channel_name = channel_name

                if YukiData.settings["channellogos"] != 3:
                    try:
                        channel_logo1 = ""
                        if "tvg-logo" in YukiData.array[i]:
                            channel_logo1 = YukiData.array[i]["tvg-logo"]

                        epg_logo1 = ""
                        if epg_id:
                            epg_icon = get_epg_icon(epg_id)
                            if epg_icon:
                                epg_logo1 = epg_icon

                        req_data_ua, req_data_ref = get_ua_ref_for_channel(
                            original_channel_name
                        )
                        channel_logos_request[YukiData.array[i]["title"]] = [
                            channel_logo1,
                            epg_logo1,
                            req_data_ua,
                            req_data_ref,
                        ]
                    except Exception:
                        logger.warning(f"Exception in channel logos (channel '{i}')")
                        logger.warning(traceback.format_exc())

                unicode_play_symbol = chr(9654) + " "
                append_symbol = ""
                if YukiData.playing_channel == channel_name:
                    append_symbol = unicode_play_symbol
                MyPlaylistWidget.name_label.setText(
                    append_symbol + str(k) + ". " + channel_name
                )
                orig_prog = prog
                try:
                    tooltip_group = "{}: {}".format(
                        _("Group"), YukiData.array[i]["tvg-group"]
                    )
                except Exception:
                    tooltip_group = "{}: {}".format(_("Group"), _("All channels"))
                if (
                    epg_found
                    and orig_prog
                    and not YukiData.settings["hideepgfromplaylist"]
                ):
                    desc1 = ""
                    wrap_desc = 40
                    if orig_desc:
                        if YukiData.settings["description_view"] == 0:
                            desc_wrapped = textwrap.fill(
                                (f"({orig_category}) " if orig_category else "")
                                + orig_desc,
                                wrap_desc,
                            ).split("\n")
                            if len(desc_wrapped) > 2:
                                desc_wrapped = desc_wrapped[:2]
                                desc_wrapped[1] = desc_wrapped[1][:-3] + "..."
                            desc_wrapped = "<br>".join(desc_wrapped)
                            desc1 = "<br>" + desc_wrapped
                        elif YukiData.settings["description_view"] == 1:
                            desc1 = "<br>" + "<br>".join(
                                textwrap.fill(
                                    (
                                        (f"({orig_category}) " if orig_category else "")
                                        + orig_desc
                                    ),
                                    wrap_desc,
                                ).split("\n")
                            )
                    MyPlaylistWidget.setDescription(
                        "<i>" + prog + "</i>" + desc1,
                        (
                            f"<b>{i}</b>" + f"<br>{tooltip_group}<br><br>"
                            "<i>" + orig_prog + "</i>" + prog_desc
                        ).replace("\n", "<br>"),
                    )
                    MyPlaylistWidget.showDescription()
                    try:
                        if start_time:
                            MyPlaylistWidget.progress_label.setText(start_time)
                            MyPlaylistWidget.end_label.setText(stop_time)
                            MyPlaylistWidget.progress_bar.setValue(int(percentage))
                        else:
                            MyPlaylistWidget.progress_bar.hide()
                    except Exception:
                        logger.warning("Async EPG load problem, ignoring")
                else:
                    MyPlaylistWidget.setDescription(
                        "", f"<b>{i}</b><br>{tooltip_group}"
                    )
                    MyPlaylistWidget.progress_bar.hide()
                    MyPlaylistWidget.hideDescription()

                MyPlaylistWidget.setPixmap(YukiGUI.tv_icon)

                if YukiData.settings["channellogos"] != 3:  # Do not load any logos
                    try:
                        if (
                            f"LOGO:::{original_channel_name}"
                            in YukiData.mp_manager_dict
                        ):
                            if YukiData.settings["channellogos"] == 0:  # Prefer M3U
                                first_loaded = False
                                if YukiData.mp_manager_dict[
                                    f"LOGO:::{original_channel_name}"
                                ][0]:
                                    channel_logo = get_pixmap_from_filename(
                                        YukiData.mp_manager_dict[
                                            f"LOGO:::{original_channel_name}"
                                        ][0]
                                    )
                                    if channel_logo:
                                        first_loaded = True
                                        MyPlaylistWidget.setPixmap(channel_logo)
                                if not first_loaded:
                                    channel_logo = get_pixmap_from_filename(
                                        YukiData.mp_manager_dict[
                                            f"LOGO:::{original_channel_name}"
                                        ][1]
                                    )
                                    if channel_logo:
                                        MyPlaylistWidget.setPixmap(channel_logo)
                            elif YukiData.settings["channellogos"] == 1:  # Prefer EPG
                                first_loaded = False
                                if YukiData.mp_manager_dict[
                                    f"LOGO:::{original_channel_name}"
                                ][1]:
                                    channel_logo = get_pixmap_from_filename(
                                        YukiData.mp_manager_dict[
                                            f"LOGO:::{original_channel_name}"
                                        ][1]
                                    )
                                    if channel_logo:
                                        first_loaded = True
                                        MyPlaylistWidget.setPixmap(channel_logo)
                                if not first_loaded:
                                    channel_logo = get_pixmap_from_filename(
                                        YukiData.mp_manager_dict[
                                            f"LOGO:::{original_channel_name}"
                                        ][0]
                                    )
                                    if channel_logo:
                                        MyPlaylistWidget.setPixmap(channel_logo)
                            elif (
                                YukiData.settings["channellogos"] == 2
                            ):  # Do not load from EPG (only M3U)
                                if YukiData.mp_manager_dict[
                                    f"LOGO:::{original_channel_name}"
                                ][0]:
                                    channel_logo = get_pixmap_from_filename(
                                        YukiData.mp_manager_dict[
                                            f"LOGO:::{original_channel_name}"
                                        ][0]
                                    )
                                    if channel_logo:
                                        MyPlaylistWidget.setPixmap(channel_logo)
                    except Exception:
                        logger.warning("Set channel logos failed with exception")
                        logger.warning(traceback.format_exc())

                myQListWidgetItem = QtWidgets.QListWidgetItem()
                myQListWidgetItem.setData(QtCore.Qt.ItemDataRole.UserRole, i)
                myQListWidgetItem.setSizeHint(
                    QtCore.QSize(
                        win.listWidget.sizeHint().width(),
                        MyPlaylistWidget.sizeHint().height(),
                    )
                )
                res[k0] = [myQListWidgetItem, MyPlaylistWidget, k0, i]
            j1 = YukiData.playing_channel
            if j1:
                current_programme = None
                epg_id = get_epg_id(j1)
                if epg_id:
                    programme = get_current_programme(epg_id)
                    if programme:
                        current_programme = programme
                show_progress(current_programme)

            # Fetch channel logos
            try:
                if YukiData.settings["channellogos"] != 3:
                    if channel_logos_request != YukiData.channel_logos_request_old:
                        YukiData.channel_logos_request_old = channel_logos_request
                        logger.debug("Channel logos request")
                        if (
                            YukiData.channel_logos_process
                            and YukiData.channel_logos_process.is_alive()
                        ):
                            # logger.debug(
                            #     "Old channel logos request found, stopping it"
                            # )
                            YukiData.channel_logos_process.kill()
                        YukiData.channel_logos_process = get_context("spawn").Process(
                            name="[yuki-iptv] channel_logos_worker",
                            target=channel_logos_worker,
                            daemon=True,
                            args=(
                                channel_logos_request,
                                YukiData.mp_manager_dict,
                            ),
                        )
                        YukiData.channel_logos_process.start()
            except Exception:
                logger.warning("Fetch channel logos failed with exception:")
                logger.warning(traceback.format_exc())

            return res

        def destroy_listwidget_items(listwidget):
            try:
                for x in range(listwidget.count()):
                    try:
                        listwidget.itemWidget(listwidget.item(x)).destroy()
                    except Exception:
                        pass
            except Exception:
                pass

        def redraw_channels():
            channels_1 = generate_channels()
            update_tvguide()
            YukiData.row0 = win.listWidget.currentRow()
            val0 = win.listWidget.verticalScrollBar().value()
            destroy_listwidget_items(win.listWidget)
            win.listWidget.clear()
            if channels_1:
                for channel_1 in channels_1.values():
                    channel_3 = channel_1
                    win.listWidget.addItem(channel_3[0])
                    win.listWidget.setItemWidget(channel_3[0], channel_3[1])
            else:
                win.listWidget.addItem(_("Nothing found"))
            win.listWidget.setCurrentRow(YukiData.row0)
            win.listWidget.verticalScrollBar().setValue(val0)

        def group_change(self):
            YukiData.comboboxIndex = YukiData.combobox.currentIndex()
            YukiData.current_group = groups[self]
            if not YukiData.first_change:
                YukiData.first_change = True
            else:
                execute_in_main_thread(partial(redraw_channels))

        def playmode_change(self=False):
            YukiData.playmodeIndex = playmode_selector.currentIndex()
            if not YukiData.first_playmode_change:
                YukiData.first_playmode_change = True
            else:
                tv_widgets = [YukiData.combobox, win.listWidget, YukiGUI.widget4]
                movies_widgets = [movies_combobox, win.moviesWidget]
                series_widgets = [win.seriesWidget]
                # Clear search text when play mode is changed
                # (TV channels, movies, series)
                try:
                    YukiGUI.channelfilter.setText("")
                    YukiGUI.channelfiltersearch.click()
                except Exception:
                    pass
                if playmode_selector.currentIndex() == 0:
                    # TV channels
                    for lbl5 in movies_widgets:
                        lbl5.hide()
                    for lbl6 in series_widgets:
                        lbl6.hide()
                    for lbl4 in tv_widgets:
                        lbl4.show()
                    try:
                        YukiGUI.channelfilter.setPlaceholderText(_("Search channel"))
                    except Exception:
                        pass
                if playmode_selector.currentIndex() == 1:
                    # Movies
                    for lbl4 in tv_widgets:
                        lbl4.hide()
                    for lbl6 in series_widgets:
                        lbl6.hide()
                    for lbl5 in movies_widgets:
                        lbl5.show()
                    try:
                        YukiGUI.channelfilter.setPlaceholderText(_("Search movie"))
                    except Exception:
                        pass
                if playmode_selector.currentIndex() == 2:
                    # Series
                    for lbl4 in tv_widgets:
                        lbl4.hide()
                    for lbl5 in movies_widgets:
                        lbl5.hide()
                    for lbl6 in series_widgets:
                        lbl6.show()
                    try:
                        YukiGUI.channelfilter.setPlaceholderText(_("Search series"))
                    except Exception:
                        pass

        channels = generate_channels()
        for channel in channels:
            win.listWidget.addItem(channels[channel][0])
            win.listWidget.setItemWidget(channels[channel][0], channels[channel][1])

        def sort_upbtn_clicked():
            curIndex = YukiGUI.sort_list.currentRow()
            if curIndex != -1 and curIndex > 0:
                curItem = YukiGUI.sort_list.takeItem(curIndex)
                YukiGUI.sort_list.insertItem(curIndex - 1, curItem)
                YukiGUI.sort_list.setCurrentRow(curIndex - 1)

        def sort_downbtn_clicked():
            curIndex1 = YukiGUI.sort_list.currentRow()
            if curIndex1 != -1 and curIndex1 < YukiGUI.sort_list.count() - 1:
                curItem1 = YukiGUI.sort_list.takeItem(curIndex1)
                YukiGUI.sort_list.insertItem(curIndex1 + 1, curItem1)
                YukiGUI.sort_list.setCurrentRow(curIndex1 + 1)

        YukiGUI.create_sort_widgets2()

        YukiGUI.sort_upbtn.clicked.connect(sort_upbtn_clicked)
        YukiGUI.sort_downbtn.clicked.connect(sort_downbtn_clicked)

        def tvguide_context_menu():
            update_tvguide()
            YukiData.tvguide_lbl.show()
            tvguide_close_lbl.show()

        def settings_context_menu():
            if YukiGUI.channels_win.isVisible():
                YukiGUI.channels_win.close()
            YukiGUI.title.setText(str(YukiData.item_selected))
            if (
                YukiData.settings["m3u"] in YukiData.channel_sets
                and YukiData.item_selected
                in YukiData.channel_sets[YukiData.settings["m3u"]]
            ):
                YukiGUI.deinterlace_chk.setChecked(
                    YukiData.channel_sets[YukiData.settings["m3u"]][
                        YukiData.item_selected
                    ]["deinterlace"]
                )
                try:
                    YukiGUI.useragent_choose.setText(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["ua"]
                    )
                except Exception:
                    YukiGUI.useragent_choose.setText("")
                try:
                    YukiGUI.referer_choose_custom.setText(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["ref"]
                    )
                except Exception:
                    YukiGUI.referer_choose_custom.setText("")
                try:
                    YukiGUI.group_text.setText(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["group"]
                    )
                except Exception:
                    YukiGUI.group_text.setText("")
                try:
                    YukiGUI.hidden_chk.setChecked(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["hidden"]
                    )
                except Exception:
                    YukiGUI.hidden_chk.setChecked(False)
                try:
                    YukiGUI.contrast_choose.setValue(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["contrast"]
                    )
                except Exception:
                    YukiGUI.contrast_choose.setValue(0)
                try:
                    YukiGUI.brightness_choose.setValue(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["brightness"]
                    )
                except Exception:
                    YukiGUI.brightness_choose.setValue(0)
                try:
                    YukiGUI.hue_choose.setValue(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["hue"]
                    )
                except Exception:
                    YukiGUI.hue_choose.setValue(0)
                try:
                    YukiGUI.saturation_choose.setValue(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["saturation"]
                    )
                except Exception:
                    YukiGUI.saturation_choose.setValue(0)
                try:
                    YukiGUI.gamma_choose.setValue(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["gamma"]
                    )
                except Exception:
                    YukiGUI.gamma_choose.setValue(0)
                try:
                    YukiGUI.videoaspect_choose.setCurrentIndex(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["videoaspect"]
                    )
                except Exception:
                    YukiGUI.videoaspect_choose.setCurrentIndex(0)
                try:
                    YukiGUI.zoom_choose.setCurrentIndex(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["zoom"]
                    )
                except Exception:
                    YukiGUI.zoom_choose.setCurrentIndex(0)
                try:
                    YukiGUI.panscan_choose.setValue(
                        YukiData.channel_sets[YukiData.settings["m3u"]][
                            YukiData.item_selected
                        ]["panscan"]
                    )
                except Exception:
                    YukiGUI.panscan_choose.setValue(0)
                try:
                    epgname_saved = YukiData.channel_sets[YukiData.settings["m3u"]][
                        YukiData.item_selected
                    ]["epgname"]
                    if not epgname_saved:
                        epgname_saved = _("Default")
                    YukiGUI.epgname_lbl.setText(epgname_saved)
                except Exception:
                    YukiGUI.epgname_lbl.setText(_("Default"))
            else:
                YukiGUI.deinterlace_chk.setChecked(YukiData.settings["deinterlace"])
                YukiGUI.hidden_chk.setChecked(False)
                YukiGUI.contrast_choose.setValue(0)
                YukiGUI.brightness_choose.setValue(0)
                YukiGUI.hue_choose.setValue(0)
                YukiGUI.saturation_choose.setValue(0)
                YukiGUI.gamma_choose.setValue(0)
                YukiGUI.videoaspect_choose.setCurrentIndex(0)
                YukiGUI.zoom_choose.setCurrentIndex(0)
                YukiGUI.panscan_choose.setValue(0)
                YukiGUI.useragent_choose.setText("")
                YukiGUI.referer_choose_custom.setText("")
                YukiGUI.group_text.setText("")
                YukiGUI.epgname_lbl.setText(_("Default"))
            move_window_to_center(YukiGUI.channels_win)
            YukiGUI.channels_win.show()

        def tvguide_favourites_add():
            if YukiData.item_selected in YukiData.favourite_sets:
                isdelete_fav_msg = QtWidgets.QMessageBox.question(
                    None,
                    "yuki-iptv",
                    str(_("Delete from favourites")) + "?",
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No,
                    QtWidgets.QMessageBox.StandardButton.Yes,
                )
                if isdelete_fav_msg == QtWidgets.QMessageBox.StandardButton.Yes:
                    YukiData.favourite_sets.remove(YukiData.item_selected)
            else:
                YukiData.favourite_sets.append(YukiData.item_selected)
            save_favourite_sets()
            execute_in_main_thread(partial(redraw_channels))

        def open_external_player():
            move_window_to_center(YukiGUI.ext_win)
            YukiGUI.ext_win.show()

        def tvguide_hide():
            YukiData.tvguide_lbl.setText("")
            YukiData.tvguide_lbl.hide()
            tvguide_close_lbl.hide()

        def favoritesplaylistsep_add():
            ps_data = getArrayItem(YukiData.item_selected)
            str1 = "#EXTINF:-1"
            if ps_data["tvg-name"]:
                str1 += f" tvg-name=\"{ps_data['tvg-name']}\""
            if ps_data["tvg-ID"]:
                str1 += f" tvg-id=\"{ps_data['tvg-ID']}\""
            if ps_data["tvg-logo"]:
                str1 += f" tvg-logo=\"{ps_data['tvg-logo']}\""
            if ps_data["tvg-group"]:
                str1 += f" tvg-group=\"{ps_data['tvg-group']}\""
            if ps_data["tvg-url"]:
                str1 += f" tvg-url=\"{ps_data['tvg-url']}\""
            else:
                str1 += f" tvg-url=\"{YukiData.settings['epg']}\""
            if ps_data["catchup"]:
                str1 += f" catchup=\"{ps_data['catchup']}\""
            if ps_data["catchup-source"]:
                str1 += f" catchup-source=\"{ps_data['catchup-source']}\""
            if ps_data["catchup-days"]:
                str1 += f" catchup-days=\"{ps_data['catchup-days']}\""

            str_append = ""
            if ps_data["useragent"]:
                str_append += f"#EXTVLCOPT:http-user-agent={ps_data['useragent']}\n"
            if ps_data["referer"]:
                str_append += f"#EXTVLCOPT:http-referrer={ps_data['referer']}\n"

            str1 += f",{YukiData.item_selected}\n{str_append}{ps_data['url']}\n"
            file03 = open(str(Path(LOCAL_DIR, "favplaylist.m3u")), encoding="utf8")
            file03_contents = file03.read()
            file03.close()
            if file03_contents == "#EXTM3U\n#EXTINF:-1,-\nhttp://255.255.255.255\n":
                file04 = open(
                    str(Path(LOCAL_DIR, "favplaylist.m3u")), "w", encoding="utf8"
                )
                file04.write("#EXTM3U\n" + str1)
                file04.close()
            else:
                if str1 in file03_contents:
                    playlistsep_del_msg = QtWidgets.QMessageBox.question(
                        None,
                        "yuki-iptv",
                        _("Remove channel from Favourites+?"),
                        QtWidgets.QMessageBox.StandardButton.Yes
                        | QtWidgets.QMessageBox.StandardButton.No,
                        QtWidgets.QMessageBox.StandardButton.Yes,
                    )
                    if playlistsep_del_msg == QtWidgets.QMessageBox.StandardButton.Yes:
                        new_data = file03_contents.replace(str1, "")
                        if new_data == "#EXTM3U\n":
                            new_data = "#EXTM3U\n#EXTINF:-1,-\nhttp://255.255.255.255\n"
                        file05 = open(
                            str(Path(LOCAL_DIR, "favplaylist.m3u")),
                            "w",
                            encoding="utf8",
                        )
                        file05.write(new_data)
                        file05.close()
                else:
                    file02 = open(
                        str(Path(LOCAL_DIR, "favplaylist.m3u")), "w", encoding="utf8"
                    )
                    file02.write(file03_contents + str1)
                    file02.close()

        def show_context_menu(pos):
            is_continue = True
            try:
                is_continue = win.listWidget.selectedItems()[0].text() != _(
                    "Nothing found"
                )
            except Exception:
                pass
            try:
                if is_continue:
                    self = win.listWidget
                    itemSelected_event(self.selectedItems()[0])
                    menu = QtWidgets.QMenu(self)
                    menu.addAction(_("TV guide"), tvguide_context_menu)
                    menu.addAction(_("Hide TV guide"), tvguide_hide)
                    menu.addAction(_("Favourites"), tvguide_favourites_add)
                    menu.addAction(
                        _("Favourites+ (separate playlist)"), favoritesplaylistsep_add
                    )
                    menu.addAction(_("Open in external player"), open_external_player)
                    menu.addAction(_("Video settings"), settings_context_menu)
                    menu.exec(self.mapToGlobal(pos))
            except Exception:
                pass

        win.listWidget.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        win.listWidget.customContextMenuRequested.connect(show_context_menu)
        win.listWidget.currentItemChanged.connect(itemSelected_event)
        win.listWidget.itemClicked.connect(itemSelected_event)
        win.listWidget.itemDoubleClicked.connect(itemClicked_event)

        def enterPressed():
            currentItem1 = win.listWidget.currentItem()
            if currentItem1:
                itemClicked_event(currentItem1)

        shortcuts = {}
        shortcuts_return = QtGui.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key.Key_Return),
            win.listWidget,
            activated=enterPressed,
        )

        def get_movie_text(movie_1):
            movie_1_txt = ""
            try:
                movie_1_txt = movie_1.text()
            except Exception:
                pass
            try:
                movie_1_txt = movie_1.data(QtCore.Qt.ItemDataRole.UserRole)
            except Exception:
                pass
            if not movie_1_txt:
                movie_1_txt = ""
            return movie_1_txt

        def channelfilter_do():
            try:
                filter_txt1 = YukiGUI.channelfilter.text()
            except Exception:
                filter_txt1 = ""
            YukiData.search = filter_txt1
            if YukiData.playmodeIndex == 0:  # TV channels
                execute_in_main_thread(partial(redraw_channels))
            elif YukiData.playmodeIndex == 1:  # Movies
                for item3 in range(win.moviesWidget.count()):
                    if (
                        filter_txt1.lower().strip()
                        in get_movie_text(win.moviesWidget.item(item3)).lower().strip()
                    ):
                        win.moviesWidget.item(item3).setHidden(False)
                    else:
                        win.moviesWidget.item(item3).setHidden(True)
            elif YukiData.playmodeIndex == 2:  # Series
                try:
                    redraw_series()
                except Exception:
                    logger.warning("redraw_series FAILED")
                for item4 in range(win.seriesWidget.count()):
                    if (
                        filter_txt1.lower().strip()
                        in win.seriesWidget.item(item4).text().lower().strip()
                    ):
                        win.seriesWidget.item(item4).setHidden(False)
                    else:
                        win.seriesWidget.item(item4).setHidden(True)

        loading = QtWidgets.QLabel(_("Loading..."))
        loading.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        loading.setFont(YukiGUI.font_italic_medium)
        hideLoading()

        loading.setFont(YukiGUI.font_12_bold)
        YukiData.combobox = QtWidgets.QComboBox()
        YukiData.combobox.currentIndexChanged.connect(group_change)

        if YukiData.settings["sort_categories"] == 1:
            groups_sorted = sorted(groups)
        elif YukiData.settings["sort_categories"] == 2:
            groups_sorted = sorted(groups, reverse=True)
        else:
            groups_sorted = groups

        if YukiData.settings["sort_categories"] in (1, 2):
            groups_sorted.remove(_("All channels"))
            YukiData.combobox.addItem(_("All channels"))

            groups_sorted.remove(_("Favourites"))
            YukiData.combobox.addItem(_("Favourites"))

        YukiData.groups_sorted = groups_sorted

        for group in groups_sorted:
            YukiData.combobox.addItem(group)

        def update_movie_icons():
            if YukiData.settings["channellogos"] != 3:  # Do not load any logos
                try:
                    for item4 in range(win.moviesWidget.count()):
                        movie_name = get_movie_text(win.moviesWidget.item(item4))
                        if movie_name:
                            if f"LOGOmovie:::{movie_name}" in YukiData.mp_manager_dict:
                                if YukiData.mp_manager_dict[
                                    f"LOGOmovie:::{movie_name}"
                                ][0]:
                                    movie_logo = get_pixmap_from_filename(
                                        YukiData.mp_manager_dict[
                                            f"LOGOmovie:::{movie_name}"
                                        ][0]
                                    )
                                    if movie_logo:
                                        win.moviesWidget.itemWidget(
                                            win.moviesWidget.item(item4)
                                        ).setPixmap(movie_logo)
                except Exception:
                    logger.warning("Set movie logos failed with exception")
                    logger.warning(traceback.format_exc())

        def movies_group_change():
            if YukiData.movies:
                current_movies_group = movies_combobox.currentText()
                if current_movies_group:
                    destroy_listwidget_items(win.moviesWidget)
                    win.moviesWidget.clear()
                    YukiData.currentMoviesGroup = {}
                    movie_logos_request = {}
                    for movies1 in YukiData.movies:
                        if "tvg-group" in YukiData.movies[movies1]:
                            if (
                                YukiData.movies[movies1]["tvg-group"]
                                == current_movies_group
                            ):
                                MovieWidget = YukiGUI.PlaylistWidget(
                                    YukiGUI, YukiData.settings["hidechannellogos"]
                                )
                                MovieWidget.name_label.setText(
                                    YukiData.movies[movies1]["title"]
                                )
                                MovieWidget.progress_bar.hide()
                                MovieWidget.hideDescription()
                                MovieWidget.setPixmap(YukiGUI.movie_icon)
                                myMovieQListWidgetItem = QtWidgets.QListWidgetItem()
                                myMovieQListWidgetItem.setData(
                                    QtCore.Qt.ItemDataRole.UserRole,
                                    YukiData.movies[movies1]["title"],
                                )
                                myMovieQListWidgetItem.setSizeHint(
                                    MovieWidget.sizeHint()
                                )
                                win.moviesWidget.addItem(myMovieQListWidgetItem)
                                win.moviesWidget.setItemWidget(
                                    myMovieQListWidgetItem, MovieWidget
                                )
                                YukiData.currentMoviesGroup[
                                    YukiData.movies[movies1]["title"]
                                ] = YukiData.movies[movies1]
                                req_data_ua1, req_data_ref1 = get_ua_ref_for_channel(
                                    YukiData.movies[movies1]["title"]
                                )
                                movie_logo1 = ""
                                if "tvg-logo" in YukiData.movies[movies1]:
                                    movie_logo1 = YukiData.movies[movies1]["tvg-logo"]
                                movie_logos_request[
                                    YukiData.movies[movies1]["title"]
                                ] = [
                                    movie_logo1,
                                    "",
                                    req_data_ua1,
                                    req_data_ref1,
                                ]
                    # Fetch movie logos
                    try:
                        if YukiData.settings["channellogos"] != 3:
                            if movie_logos_request != YukiData.movie_logos_request_old:
                                YukiData.movie_logos_request_old = movie_logos_request
                                logger.debug("Movie logos request")
                                if (
                                    YukiData.movie_logos_process
                                    and YukiData.movie_logos_process.is_alive()
                                ):
                                    # logger.debug(
                                    #     "Old movie logos request found, stopping it"
                                    # )
                                    YukiData.movie_logos_process.kill()
                                YukiData.movie_logos_process = get_context(
                                    "spawn"
                                ).Process(
                                    name="[yuki-iptv] channel_logos_worker_for_movie",
                                    target=channel_logos_worker,
                                    daemon=True,
                                    args=(
                                        movie_logos_request,
                                        YukiData.mp_manager_dict,
                                        "movie",
                                    ),
                                )
                                YukiData.movie_logos_process.start()
                    except Exception:
                        logger.warning("Fetch movie logos failed with exception:")
                        logger.warning(traceback.format_exc())
                    update_movie_icons()
            else:
                destroy_listwidget_items(win.moviesWidget)
                win.moviesWidget.clear()
                win.moviesWidget.addItem(_("Nothing found"))

        def movies_play(mov_item):
            if get_movie_text(mov_item) in YukiData.currentMoviesGroup:
                itemClicked_event(
                    get_movie_text(mov_item),
                    YukiData.currentMoviesGroup[get_movie_text(mov_item)]["url"],
                )

        win.moviesWidget.itemDoubleClicked.connect(movies_play)

        movies_groups = []
        movies_combobox = QtWidgets.QComboBox()
        for movie_combobox in YukiData.movies:
            if "tvg-group" in YukiData.movies[movie_combobox]:
                if YukiData.movies[movie_combobox]["tvg-group"] not in movies_groups:
                    movies_groups.append(YukiData.movies[movie_combobox]["tvg-group"])
        for movie_group in movies_groups:
            movies_combobox.addItem(movie_group)
        movies_combobox.currentIndexChanged.connect(movies_group_change)
        movies_group_change()

        def redraw_series():
            YukiData.serie_selected = False
            win.seriesWidget.clear()
            if YukiData.series:
                for serie2 in YukiData.series:
                    win.seriesWidget.addItem(serie2)
            else:
                win.seriesWidget.addItem(_("Nothing found"))

        def series_change_pt2(sel_serie):
            YukiGUI.channelfilter.setDisabled(False)
            YukiGUI.channelfiltersearch.setDisabled(False)
            win.seriesWidget.clear()
            win.seriesWidget.addItem("< " + _("Back"))
            win.seriesWidget.item(0).setForeground(QtCore.Qt.GlobalColor.blue)
            for season_name in YukiData.series[sel_serie].seasons.keys():
                season = YukiData.series[sel_serie].seasons[season_name]
                season_item = QtWidgets.QListWidgetItem()
                season_item.setText(season.name)
                season_item.setFont(YukiGUI.font_bold)
                win.seriesWidget.addItem(season_item)
                for episode_name in season.episodes.keys():
                    episode = season.episodes[episode_name]
                    episode_item = QtWidgets.QListWidgetItem()
                    episode_item.setText(episode.title)
                    episode_item.setData(
                        QtCore.Qt.ItemDataRole.UserRole,
                        episode.url
                        + ":::::::::::::::::::"
                        + season.name
                        + ":::::::::::::::::::"
                        + sel_serie,
                    )
                    win.seriesWidget.addItem(episode_item)
            YukiData.serie_selected = True

        def series_loading():
            YukiGUI.channelfilter.setDisabled(True)
            YukiGUI.channelfiltersearch.setDisabled(True)
            win.seriesWidget.clear()
            win.seriesWidget.addItem(_("Loading..."))

        def series_load(sel_serie):
            if not YukiData.series[sel_serie].seasons:
                logger.info(f"Fetching data for serie '{sel_serie}'")
                execute_in_main_thread(partial(series_loading))
                try:
                    xt.get_series_info_by_id(YukiData.series[sel_serie])
                    logger.info(
                        f"Fetching data for serie '{sel_serie}' completed"
                        f", seasons: {len(YukiData.series[sel_serie].seasons)}"
                    )
                except Exception:
                    logger.warning(f"Fetching data for serie '{sel_serie}' FAILED")
            execute_in_main_thread(partial(series_change_pt2, sel_serie))

        def series_change(series_item):
            sel_serie = series_item.text()
            if sel_serie == "< " + _("Back"):
                redraw_series()
            elif sel_serie != _("Loading..."):
                if YukiData.serie_selected:
                    try:
                        serie_data = series_item.data(QtCore.Qt.ItemDataRole.UserRole)
                        if serie_data:
                            series_name = serie_data.split(":::::::::::::::::::")[2]
                            season_name = serie_data.split(":::::::::::::::::::")[1]
                            serie_url = serie_data.split(":::::::::::::::::::")[0]
                            itemClicked_event(
                                sel_serie
                                + " ::: "
                                + season_name
                                + " ::: "
                                + series_name,
                                serie_url,
                            )
                    except Exception:
                        pass
                else:
                    thread_series_load = threading.Thread(
                        target=series_load, args=(sel_serie,), daemon=True
                    )
                    thread_series_load.start()

        win.seriesWidget.itemDoubleClicked.connect(series_change)

        redraw_series()

        playmode_selector = QtWidgets.QComboBox()
        playmode_selector.currentIndexChanged.connect(playmode_change)
        for playmode in [_("TV channels"), _("Movies"), _("Series")]:
            playmode_selector.addItem(playmode)

        def focusOutEvent_after(
            playlist_widget_visible,
            controlpanel_widget_visible,
            channelfiltersearch_has_focus,
        ):
            YukiGUI.channelfilter.usePopup = False
            YukiGUI.playlist_widget.setWindowFlags(
                QtCore.Qt.WindowType.CustomizeWindowHint
                | QtCore.Qt.WindowType.FramelessWindowHint
                | QtCore.Qt.WindowType.X11BypassWindowManagerHint
            )
            YukiGUI.controlpanel_widget.setWindowFlags(
                QtCore.Qt.WindowType.CustomizeWindowHint
                | QtCore.Qt.WindowType.FramelessWindowHint
                | QtCore.Qt.WindowType.X11BypassWindowManagerHint
            )
            if playlist_widget_visible:
                YukiGUI.playlist_widget.show()
            if controlpanel_widget_visible:
                YukiGUI.controlpanel_widget.show()
            if channelfiltersearch_has_focus:
                YukiGUI.channelfiltersearch.click()

        def mainthread_timer_2(t2):
            time.sleep(0.05)
            execute_in_main_thread(t2)

        def mainthread_timer(t1):
            thread_mainthread_timer_2 = threading.Thread(
                target=mainthread_timer_2, daemon=True
            )
            thread_mainthread_timer_2.start()

        class MyLineEdit(QtWidgets.QLineEdit):
            usePopup = False
            click_event = QtCore.pyqtSignal()

            def mousePressEvent(self, event1):
                if event1.button() == QtCore.Qt.MouseButton.LeftButton:
                    self.click_event.emit()
                else:
                    super().mousePressEvent(event1)

            def focusOutEvent(self, event2):
                super().focusOutEvent(event2)
                if YukiData.fullscreen:
                    playlist_widget_visible1 = YukiGUI.playlist_widget.isVisible()
                    controlpanel_widget_visible1 = (
                        YukiGUI.controlpanel_widget.isVisible()
                    )
                    channelfiltersearch_has_focus1 = (
                        YukiGUI.channelfiltersearch.hasFocus()
                    )
                    focusOutEvent_after_partial = partial(
                        focusOutEvent_after,
                        playlist_widget_visible1,
                        controlpanel_widget_visible1,
                        channelfiltersearch_has_focus1,
                    )
                    mainthread_timer_1 = partial(
                        mainthread_timer, focusOutEvent_after_partial
                    )
                    execute_in_main_thread(mainthread_timer_1)

        def channelfilter_clicked():
            if YukiData.fullscreen:
                playlist_widget_visible1 = YukiGUI.playlist_widget.isVisible()
                controlpanel_widget_visible1 = YukiGUI.controlpanel_widget.isVisible()
                YukiGUI.channelfilter.usePopup = True
                YukiGUI.playlist_widget.setWindowFlags(
                    QtCore.Qt.WindowType.CustomizeWindowHint
                    | QtCore.Qt.WindowType.FramelessWindowHint
                    | QtCore.Qt.WindowType.X11BypassWindowManagerHint
                    | QtCore.Qt.WindowType.Popup
                )
                YukiGUI.controlpanel_widget.setWindowFlags(
                    QtCore.Qt.WindowType.CustomizeWindowHint
                    | QtCore.Qt.WindowType.FramelessWindowHint
                    | QtCore.Qt.WindowType.X11BypassWindowManagerHint
                    | QtCore.Qt.WindowType.Popup
                )
                if playlist_widget_visible1:
                    YukiGUI.playlist_widget.show()
                if controlpanel_widget_visible1:
                    YukiGUI.controlpanel_widget.show()

        def page_change():
            win.listWidget.verticalScrollBar().setValue(0)
            redraw_channels()
            try:
                YukiGUI.page_box.clearFocus()
            except Exception:
                pass

        YukiGUI.create2(
            get_page_count(len(YukiData.array)),
            channelfilter_clicked,
            channelfilter_do,
            page_change,
            MyLineEdit,
            playmode_selector,
            YukiData.combobox,
            movies_combobox,
            loading,
        )

        if YukiData.settings["panelposition"] == 2:
            dockWidget_playlist.resize(
                DOCKWIDGET_PLAYLIST_WIDTH, dockWidget_playlist.height()
            )
            playlist_label = QtWidgets.QLabel(_("Playlist"))
            playlist_label.setFont(YukiGUI.font_12_bold)
            dockWidget_playlist.setTitleBarWidget(playlist_label)
        else:
            dockWidget_playlist.setFixedWidth(DOCKWIDGET_PLAYLIST_WIDTH)
            dockWidget_playlist.setTitleBarWidget(QtWidgets.QWidget())
        if YukiData.settings["panelposition"] == 2:
            gripWidget = QtWidgets.QWidget()
            gripLayout = QtWidgets.QVBoxLayout()
            gripLayout.setContentsMargins(0, 0, 0, 0)
            gripLayout.setSpacing(0)
            gripLayout.addWidget(YukiGUI.widget)
            gripLayout.addWidget(
                QtWidgets.QSizeGrip(YukiGUI.widget),
                0,
                QtCore.Qt.AlignmentFlag.AlignBottom
                | QtCore.Qt.AlignmentFlag.AlignRight,
            )
            gripWidget.setLayout(gripLayout)
            dockWidget_playlist.setWidget(gripWidget)
        else:
            dockWidget_playlist.setWidget(YukiGUI.widget)
        dockWidget_playlist.setFloating(YukiData.settings["panelposition"] == 2)
        dockWidget_playlist.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        )
        if YukiData.settings["panelposition"] == 0:
            win.addDockWidget(
                QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dockWidget_playlist
            )
        elif YukiData.settings["panelposition"] == 1:
            win.addDockWidget(
                QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dockWidget_playlist
            )
        elif YukiData.settings["panelposition"] == 2:
            separate_playlist_data = read_option("separate_playlist")
            if separate_playlist_data:
                dockWidget_playlist.setGeometry(
                    separate_playlist_data["x"],
                    separate_playlist_data["y"],
                    separate_playlist_data["w"],
                    separate_playlist_data["h"],
                )
            else:
                dockWidget_playlist.resize(dockWidget_playlist.width(), win.height())
                dockWidget_playlist.move(
                    win.pos().x() + win.width() - dockWidget_playlist.width() + 25,
                    win.pos().y(),
                )

        FORBIDDEN_CHARS = ('"', "*", ":", "<", ">", "?", "\\", "/", "|", "[", "]")

        def do_screenshot():
            if YukiData.playing_channel:
                YukiData.state.show()
                YukiData.state.setTextYuki(_("Doing screenshot..."))
                ch = YukiData.playing_channel.replace(" ", "_")
                for char in FORBIDDEN_CHARS:
                    ch = ch.replace(char, "")
                cur_time = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
                file_name = "screenshot_-_" + cur_time + "_-_" + ch + ".png"
                if not YukiData.settings["scrrecnosubfolders"]:
                    file_path = str(Path(save_folder, "screenshots", file_name))
                else:
                    file_path = str(Path(save_folder, file_name))
                try:
                    YukiData.player.screenshot_to_file(file_path, includes="subtitles")
                    YukiData.state.show()
                    YukiData.state.setTextYuki(_("Screenshot saved!"))
                except Exception:
                    YukiData.state.show()
                    YukiData.state.setTextYuki(_("Screenshot saving error!"))
                YukiData.time_stop = time.time() + 1
            else:
                YukiData.state.show()
                YukiData.state.setTextYuki("{}!".format(_("No channel selected")))
                YukiData.time_stop = time.time() + 1

        def update_tvguide(
            channel_1="",
            do_return=False,
            show_all_guides=False,
            mark_integers=False,
            date_selected=None,
        ):
            if YukiData.array:
                if not channel_1:
                    if YukiData.item_selected:
                        channel_2 = YukiData.item_selected
                    else:
                        channel_2 = sorted(YukiData.array.items())[0][0]
                else:
                    channel_2 = channel_1
                try:
                    channel_1_item = getArrayItem(channel_1)
                except Exception:
                    channel_1_item = None
                txt = _("No TV guide for channel")
                newline_symbol = "\n"
                if do_return:
                    newline_symbol = "!@#$%^^&*("

                current_programmes = None
                epg_id = get_epg_id(channel_2)
                if epg_id:
                    programmes = get_epg_programmes(epg_id)
                    if programmes:
                        current_programmes = programmes

                if current_programmes:
                    txt = newline_symbol
                    for pr in current_programmes:
                        override_this = False
                        if show_all_guides:
                            override_this = pr["start"] < time.time() + 1
                        else:
                            override_this = pr["stop"] > time.time() - 1
                        archive_btn = ""
                        if date_selected is not None:
                            override_this = epg_is_in_date(pr, date_selected)
                        if override_this:
                            use_placeholder = "%d.%m.%y %H:%M"
                            if mark_integers:
                                use_placeholder = "%d.%m.%Y %H:%M:%S"
                            start_2 = (
                                datetime.datetime.fromtimestamp(pr["start"]).strftime(
                                    use_placeholder
                                )
                                + " - "
                            )
                            stop_2 = (
                                datetime.datetime.fromtimestamp(pr["stop"]).strftime(
                                    use_placeholder
                                )
                                + "\n"
                            )
                            try:
                                title_2 = pr["title"] if "title" in pr else ""
                            except Exception:
                                title_2 = ""
                            try:
                                desc_2 = (
                                    ("\n" + pr["desc"] + "\n") if "desc" in pr else ""
                                )
                            except Exception:
                                desc_2 = ""
                            attach_1 = ""
                            if mark_integers:
                                try:
                                    marked_integer = current_programmes.index(pr)
                                except Exception:
                                    marked_integer = -1
                                attach_1 = f" ({marked_integer})"
                            if (
                                date_selected is not None
                                and YukiGUI.showonlychplaylist_chk.isChecked()
                            ):
                                try:
                                    catchup_days2 = int(channel_1_item["catchup-days"])
                                except Exception:
                                    catchup_days2 = 7
                                # support for seconds
                                if catchup_days2 < 1000:
                                    catchup_days2 = catchup_days2 * 86400
                                if (
                                    pr["start"] < time.time() + 1
                                    and not (
                                        time.time() > pr["start"]
                                        and time.time() < pr["stop"]
                                    )
                                    and pr["stop"] > time.time() - catchup_days2
                                ):
                                    archive_link = urllib.parse.quote_plus(
                                        json.dumps(
                                            [
                                                channel_1,
                                                datetime.datetime.fromtimestamp(
                                                    pr["start"]
                                                ).strftime("%d.%m.%Y %H:%M:%S"),
                                                datetime.datetime.fromtimestamp(
                                                    pr["stop"]
                                                ).strftime("%d.%m.%Y %H:%M:%S"),
                                                current_programmes.index(pr),
                                            ]
                                        )
                                    )
                                    archive_btn = (
                                        '\n<a href="#__archive__'
                                        + archive_link
                                        + '">'
                                        + _("Open archive")
                                        + "</a>"
                                    )
                            start_symbl = ""
                            stop_symbl = ""
                            if YukiData.use_dark_icon_theme:
                                start_symbl = '<span style="color: white;">'
                                stop_symbl = "</span>"
                            use_epg_color = "green"
                            if time.time() > pr["start"] and time.time() < pr["stop"]:
                                use_epg_color = "red"
                            txt += (
                                f'<span style="color: {use_epg_color};">'
                                + start_2
                                + stop_2
                                + "</span>"
                                + start_symbl
                                + "<b>"
                                + title_2
                                + "</b>"
                                + archive_btn
                                + desc_2
                                + attach_1
                                + stop_symbl
                                + newline_symbol
                            )
                if txt == newline_symbol or not txt:
                    txt = _("No TV guide for channel")
                if do_return:
                    return txt
                txt = txt.replace("\n", "<br>").replace("<br>", "", 1)
                YukiData.tvguide_lbl.setText(txt)
            return ""

        def show_tvguide():
            if YukiData.tvguide_lbl.isVisible():
                YukiData.tvguide_lbl.setText("")
                YukiData.tvguide_lbl.hide()
                tvguide_close_lbl.hide()
            else:
                update_tvguide()
                YukiData.tvguide_lbl.show()
                tvguide_close_lbl.show()

        def hide_tvguide():
            if YukiData.tvguide_lbl.isVisible():
                YukiData.tvguide_lbl.setText("")
                YukiData.tvguide_lbl.hide()
                tvguide_close_lbl.hide()

        def update_tvguide_2():
            YukiGUI.epg_win_checkbox.clear()
            if YukiGUI.showonlychplaylist_chk.isChecked():
                YukiGUI.epg_win_count.setText(
                    "({}: {})".format(_("channels"), len(YukiData.array_sorted))
                )
                for channel_0 in YukiData.array_sorted:
                    YukiGUI.epg_win_checkbox.addItem(channel_0)
            else:
                epg_names = get_all_epg_names()
                if not epg_names:
                    epg_names = set()
                YukiGUI.epg_win_count.setText(
                    "({}: {})".format(_("channels"), len(epg_names))
                )
                for channel_0 in epg_names:
                    YukiGUI.epg_win_checkbox.addItem(channel_0)

        def show_tvguide_2():
            if YukiGUI.epg_win.isVisible():
                YukiGUI.epg_win.hide()
            else:
                epg_index = YukiGUI.epg_win_checkbox.currentIndex()
                update_tvguide_2()
                if epg_index != -1:
                    YukiGUI.epg_win_checkbox.setCurrentIndex(epg_index)
                move_window_to_center(YukiGUI.epg_win)
                YukiGUI.epg_win.show()

        def get_channels_page(group, page):
            if isinstance(YukiData.array_sorted, list):
                channels = YukiData.array_sorted
            else:
                channels = list(YukiData.array_sorted.keys())
            if group and group != _("All channels"):
                if group == _("Favourites"):
                    channels = [
                        channel
                        for channel in channels
                        if channel in YukiData.favourite_sets
                    ]
                else:
                    channels = [
                        channel
                        for channel in channels
                        if YukiData.array[channel]["tvg-group"] == group
                    ]
            channels_on_page = 10
            page_start = (page * channels_on_page) - channels_on_page
            page_end = page * channels_on_page
            return channels[page_start:page_end]

        def show_multi_epg():
            if YukiGUI.multiepg_win.isVisible():
                YukiGUI.multiepg_win.hide()
            else:
                YukiGUI.multiepg_win._set(
                    getArrayItem=getArrayItem,
                    get_epg_id=get_epg_id,
                    get_epg_programmes=get_epg_programmes,
                    epg_is_in_date=epg_is_in_date,
                    font_bold=YukiGUI.font_bold,
                    font_italic=YukiGUI.font_italic,
                    get_channels_page=get_channels_page,
                    is_dark_theme=is_dark_theme,
                )
                YukiGUI.multiepg_win.first()
                YukiGUI.multiepg_win.show()

        def show_archive():
            if not YukiGUI.epg_win.isVisible():
                show_tvguide_2()
                find_channel = YukiData.item_selected
                if not find_channel:
                    find_channel = YukiData.playing_channel
                if find_channel:
                    try:
                        find_channel_index = YukiGUI.epg_win_checkbox.findText(
                            find_channel, QtCore.Qt.MatchFlag.MatchExactly
                        )
                    except Exception:
                        find_channel_index = -1
                    if find_channel_index != -1:
                        YukiGUI.epg_win_checkbox.setCurrentIndex(find_channel_index)
                epg_date_changed(YukiGUI.epg_select_date.selectedDate())
            else:
                YukiGUI.epg_win.hide()

        def start_record(ch1, url3):
            orig_channel_name = ch1
            if not YukiData.is_recording:
                YukiData.is_recording = True
                YukiGUI.lbl2.show()
                YukiGUI.lbl2.setText(_("Preparing record"))
                ch = ch1.replace(" ", "_")
                for char in FORBIDDEN_CHARS:
                    ch = ch.replace(char, "")
                cur_time = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
                if not YukiData.settings["scrrecnosubfolders"]:
                    out_file = str(
                        Path(
                            save_folder,
                            "recordings",
                            f"recording_-_{cur_time}_-_{ch}.ts",
                        )
                    )
                else:
                    out_file = str(
                        Path(
                            save_folder,
                            f"recording_-_{cur_time}_-_{ch}.ts",
                        )
                    )
                YukiData.record_file = out_file
                record(
                    url3,
                    out_file,
                    orig_channel_name,
                    f"Referer: {YukiData.settings['referer']}",
                    get_ua_ref_for_channel,
                )
            else:
                YukiData.is_recording = False
                YukiData.recording_time = 0
                stop_record()
                YukiGUI.lbl2.setText("")
                YukiGUI.lbl2.hide()

        def do_record():
            if YukiData.playing_channel:
                start_record(YukiData.playing_channel, YukiData.playing_url)
            else:
                YukiData.time_stop = time.time() + 1
                YukiData.state.show()
                YukiData.state.setTextYuki(_("No channel selected for record"))

        def my_log(mpv_loglevel1, component, message):
            mpv_log_str = f"[{mpv_loglevel1}] {component}: {message}"

            if "Invalid video timestamp: " not in str(mpv_log_str):
                if "[debug] " in str(mpv_log_str) or "[trace] " in str(mpv_log_str):
                    mpv_logger.debug(str(mpv_log_str).strip())
                elif "[warn] " in str(mpv_log_str):
                    mpv_logger.warning(str(mpv_log_str).strip())
                elif "[error] " in str(mpv_log_str):
                    mpv_logger.error(str(mpv_log_str).strip())
                elif "[fatal] " in str(mpv_log_str):
                    mpv_logger.critical(str(mpv_log_str).strip())
                else:
                    mpv_logger.info(str(mpv_log_str).strip())

            if "stream: Failed to open" in mpv_log_str:
                execute_in_main_thread(partial(end_file_error_callback, True))

        def playLastChannel():
            isPlayingLast = False
            if (
                os.path.isfile(str(Path(LOCAL_DIR, "lastchannels.json")))
                and YukiData.settings["openprevchannel"]
            ):
                try:
                    lastfile_1 = open(
                        str(Path(LOCAL_DIR, "lastchannels.json")), encoding="utf8"
                    )
                    lastfile_1_dat = json.loads(lastfile_1.read())
                    lastfile_1.close()
                    if lastfile_1_dat[0] in YukiData.array_sorted:
                        isPlayingLast = True
                        YukiData.player.user_agent = lastfile_1_dat[2]
                        setChannelText("  " + lastfile_1_dat[0])
                        itemClicked_event(lastfile_1_dat[0])
                        setChannelText("  " + lastfile_1_dat[0])
                        try:
                            if lastfile_1_dat[3] < YukiData.combobox.count():
                                YukiData.combobox.setCurrentIndex(lastfile_1_dat[3])
                        except Exception:
                            pass
                        try:
                            win.listWidget.setCurrentRow(lastfile_1_dat[4])
                        except Exception:
                            pass
                except Exception:
                    if os.path.isfile(str(Path(LOCAL_DIR, "lastchannels.json"))):
                        os.remove(str(Path(LOCAL_DIR, "lastchannels.json")))
            return isPlayingLast

        options, options_custom = get_mpv_options(
            {
                "osc": True,
                "hwdec": "no",
                "ytdl": False,
                "title": "yuki-iptv",
                "force-window": True,
                "force-seekable": True,
                "audio-client-name": "yuki-iptv",
                "wid": str(int(win.container.winId())),
                "loglevel": "info" if loglevel.lower() != "debug" else "debug",
                "script-opts": "osc-layout=slimbox,osc-seekbarstyle=bar,"
                "osc-deadzonesize=0,osc-minmousemove=3,osc-idlescreen=no",
            },
            YukiData.settings["mpv_options"],
        )

        logger.info(f"Custom mpv options: {json.dumps(options_custom)}")

        def get_about_text():
            about_txt = f"<b>yuki-iptv {APP_VERSION}</b>"
            about_txt += "<br><br>" + _("IPTV player with EPG support")
            about_txt += f"<br><br>Python {sys.version.strip()}"
            about_txt += f"<br>Qt {get_qt_info(app)}"
            about_txt += f"<br>{YukiData.player.mpv_version}"
            return about_txt

        def main_channel_settings():
            if YukiData.playing_channel:
                YukiData.item_selected = YukiData.playing_channel
                settings_context_menu()
            else:
                msg = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Icon.Warning,
                    "yuki-iptv",
                    _("No channel selected"),
                    QtWidgets.QMessageBox.StandardButton.Ok,
                )
                msg.exec()

        def idle_showhideplaylist():
            if not YukiData.fullscreen:
                try:
                    show_hide_playlist()
                except Exception:
                    pass

        def showhideplaylist():
            execute_in_main_thread(partial(idle_showhideplaylist))

        def idle_lowpanel_ch_1():
            if not YukiData.fullscreen:
                try:
                    lowpanel_ch()
                except Exception:
                    pass

        def lowpanel_ch_1():
            execute_in_main_thread(partial(idle_lowpanel_ch_1))

        def showhideeverything():
            if not YukiData.fullscreen:
                if dockWidget_playlist.isVisible():
                    YukiData.compact_mode = True
                    dockWidget_playlist.hide()
                    dockWidget_controlPanel.hide()
                    win.menu_bar_qt.hide()
                else:
                    YukiData.compact_mode = False
                    dockWidget_playlist.show()
                    dockWidget_controlPanel.show()
                    win.menu_bar_qt.show()

        def timer_bitrate():
            try:
                if YukiGUI.streaminfo_win.isVisible():
                    if "video" in stream_info.data:
                        stream_info.data["video"][0].setText(
                            stream_info.data["video"][1][_("Average Bitrate")]
                        )
                    if "audio" in stream_info.data:
                        stream_info.data["audio"][0].setText(
                            stream_info.data["audio"][1][_("Average Bitrate")]
                        )
            except Exception:
                pass

        def is_recording_func():
            ret_code_rec = False
            if YukiData.ffmpeg_processes:
                ret_code_array = []
                for ffmpeg_process_1 in YukiData.ffmpeg_processes:
                    if ffmpeg_process_1[0].processId() == 0:
                        ret_code_array.append(True)
                        YukiData.ffmpeg_processes.remove(ffmpeg_process_1)
                    else:
                        ret_code_array.append(False)
                ret_code_rec = False not in ret_code_array
            else:
                ret_code_rec = True
            return ret_code_rec

        win.oldpos = None

        def redraw_menubar():
            try:
                update_menubar(
                    YukiData.player.track_list,
                    YukiData.playing_channel,
                    YukiData.settings["m3u"],
                )
            except Exception:
                logger.warning("redraw_menubar failed")
                show_exception(traceback.format_exc(), "redraw_menubar failed")

        YukiData.right_click_menu = QtWidgets.QMenu()

        def do_reconnect():
            if YukiData.playing_channel:
                logger.info("Reconnecting to stream")
                try:
                    doPlay(*YukiData.do_play_args)
                except Exception:
                    logger.warning("Failed reconnecting to stream - no known URL")

        def do_reconnect_async():
            time.sleep(1)
            execute_in_main_thread(partial(do_reconnect))

        def end_file_error_callback(no_reconnect=False):
            logger.warning("Playing error!")
            if (
                not no_reconnect
                and YukiData.settings["autoreconnection"]
                and YukiData.playing_group == 0
            ):
                logger.warning("Connection to stream lost, waiting 1 sec...")
                thread_do_reconnect_async = threading.Thread(
                    target=do_reconnect_async, daemon=True
                )
                thread_do_reconnect_async.start()
            elif not YukiData.is_loading:
                mpv_stop()
            else:
                YukiData.resume_playback = not YukiData.player.pause
                mpv_stop()

            YukiGUI.channel.setText("")
            YukiGUI.channel.hide()
            loading.setText(_("Playing error"))
            loading.setFont(YukiGUI.font_bold_medium)
            showLoading()
            YukiGUI.loading1.hide()
            YukiGUI.loading_movie.stop()

        def end_file_callback():
            if win.isVisible():
                if YukiData.playing_channel and YukiData.player.path is None:
                    if (
                        YukiData.settings["autoreconnection"]
                        and YukiData.playing_group == 0
                    ):
                        logger.warning("Connection to stream lost, waiting 1 sec...")
                        do_reconnect_async()
                    elif not YukiData.is_loading:
                        mpv_stop()

        def file_loaded_callback():
            if YukiData.playing_channel:
                redraw_menubar()

        def my_mouse_right_callback():
            YukiData.right_click_menu.exec(QtGui.QCursor.pos())

        def my_mouse_left_callback():
            if YukiData.right_click_menu.isVisible():
                YukiData.right_click_menu.hide()
            elif YukiData.settings["hideplaylistbyleftmouseclick"]:
                show_hide_playlist()

        def idle_my_up_binding_execute():
            volume = int(YukiData.player.volume + YukiData.settings["volumechangestep"])
            volume = min(volume, 200)
            YukiGUI.volume_slider.setValue(volume)
            mpv_volume_set()

        def my_up_binding_execute():
            execute_in_main_thread(partial(idle_my_up_binding_execute))

        def idle_my_down_binding_execute():
            volume = int(YukiData.player.volume - YukiData.settings["volumechangestep"])
            volume = max(volume, 0)
            YukiData.time_stop = time.time() + 3
            show_volume(volume)
            YukiGUI.volume_slider.setValue(volume)
            mpv_volume_set()

        def my_down_binding_execute():
            execute_in_main_thread(partial(idle_my_down_binding_execute))

        class ControlPanelDockWidget(QtWidgets.QDockWidget):
            def enterEvent(self, event4):
                YukiData.check_controlpanel_visible = True

            def leaveEvent(self, event4):
                YukiData.check_controlpanel_visible = False

        dockWidget_controlPanel = ControlPanelDockWidget(win)

        dockWidget_playlist.setObjectName("dockWidget_playlist")
        dockWidget_controlPanel.setObjectName("dockWidget_controlPanel")

        def open_recording_folder():
            absolute_path = Path(save_folder).absolute()
            xdg_open = subprocess.Popen(["xdg-open", str(absolute_path)])
            xdg_open.wait()

        def open_recording_folder_async():
            thread_open_recording_folder = threading.Thread(
                target=open_recording_folder, daemon=True
            )
            thread_open_recording_folder.start()

        def go_channel(i1):
            pause_state = YukiData.player.pause
            if YukiData.resume_playback:
                YukiData.resume_playback = False
                pause_state = False
            row = win.listWidget.currentRow()
            if row == -1:
                row = YukiData.row0
            next_row = row + i1
            if next_row < 0:
                # Previous page
                if YukiGUI.page_box.value() - 1 == 0:
                    next_row = 0
                else:
                    YukiGUI.page_box.setValue(YukiGUI.page_box.value() - 1)
                    next_row = win.listWidget.count()
            elif next_row > win.listWidget.count() - 1:
                # Next page
                if YukiGUI.page_box.value() + 1 > YukiGUI.page_box.maximum():
                    next_row = row
                else:
                    YukiGUI.page_box.setValue(YukiGUI.page_box.value() + 1)
                    next_row = 0
            next_row = max(next_row, 0)
            next_row = min(next_row, win.listWidget.count() - 1)
            chk_pass = True
            try:
                chk_pass = win.listWidget.item(next_row).text() != _("Nothing found")
            except Exception:
                pass
            if chk_pass:
                win.listWidget.setCurrentRow(next_row)
                itemClicked_event(win.listWidget.currentItem())
            YukiData.player.pause = pause_state

        def prev_channel():
            execute_in_main_thread(partial(go_channel, -1))

        def next_channel():
            execute_in_main_thread(partial(go_channel, 1))

        def get_keybind(func1):
            return YukiData.main_keybinds[func1]

        def mpris_set_volume(val):
            YukiGUI.volume_slider.setValue(int(val * 100))
            mpv_volume_set()

        def mpris_seek(val):
            if YukiData.playing_channel:
                YukiData.player.command("seek", val)

        def mpris_set_position(track_id, val):
            if (
                YukiData.player
                and YukiData.mpris_ready
                and YukiData.mpris_running
                and not YukiData.stopped
            ):
                (
                    playback_status,
                    mpris_trackid,
                    artUrl,
                    player_position,
                ) = get_mpris_metadata()
                if track_id == mpris_trackid:
                    YukiData.player.time_pos = val

        def get_playlist_hash(playlist):
            return hashlib.sha512(playlist["m3u"].encode("utf-8")).hexdigest()

        def get_playlists():
            prefix = "/page/codeberg/liya/yuki_iptv/Playlist/"
            current_playlist = (f"{prefix}Unknown", _("Unknown"), "")
            current_playlist_name = _("Unknown")
            for playlist in YukiData.playlists_saved:
                if (
                    YukiData.playlists_saved[playlist]["m3u"]
                    == YukiData.settings["m3u"]
                ):
                    current_playlist_name = playlist
                    current_playlist = (
                        f"{prefix}"
                        f"{get_playlist_hash(YukiData.playlists_saved[playlist])}",
                        playlist,
                        "",
                    )
                    break
            return (
                current_playlist_name,
                current_playlist,
                [
                    (
                        f"{prefix}{get_playlist_hash(YukiData.playlists_saved[x])}",
                        x,
                        "",
                    )
                    for x in YukiData.playlists_saved
                ],
            )

        def mpris_select_playlist(playlist_to_select):
            (
                _current_playlist_name,
                _current_playlist,
                playlists,
            ) = get_playlists()
            for playlist in playlists:
                if playlist[0] == playlist_to_select:
                    playlist_selected(f"playlist:{playlist[1]}")
                    break

        try:

            def mpris_callback(mpris_data):
                if (
                    mpris_data[0] == "org.mpris.MediaPlayer2"
                    and mpris_data[1] == "Raise"
                ):
                    execute_in_main_thread(partial(lambda: show_window(win)))
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2"
                    and mpris_data[1] == "Quit"
                ):
                    QtCore.QTimer.singleShot(
                        100, lambda: execute_in_main_thread(partial(key_quit))
                    )
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Player"
                    and mpris_data[1] == "Next"
                ):
                    execute_in_main_thread(partial(next_channel))
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Player"
                    and mpris_data[1] == "Previous"
                ):
                    execute_in_main_thread(partial(prev_channel))
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Player"
                    and mpris_data[1] == "Pause"
                ):
                    if not YukiData.player.pause:
                        execute_in_main_thread(partial(mpv_play))
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Player"
                    and mpris_data[1] == "PlayPause"
                ):
                    execute_in_main_thread(partial(mpv_play))
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Player"
                    and mpris_data[1] == "Stop"
                ):
                    execute_in_main_thread(partial(mpv_stop))
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Player"
                    and mpris_data[1] == "Play"
                ):
                    if YukiData.player.pause:
                        execute_in_main_thread(partial(mpv_play))
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Player"
                    and mpris_data[1] == "Seek"
                ):
                    # microseconds to seconds
                    execute_in_main_thread(
                        partial(mpris_seek, mpris_data[2][0] / 1000000)
                    )
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Player"
                    and mpris_data[1] == "SetPosition"
                ):
                    track_id = mpris_data[2][0]
                    position = mpris_data[2][1] / 1000000  # microseconds to seconds
                    if track_id != "/page/codeberg/liya/yuki_iptv/Track/NoTrack":
                        execute_in_main_thread(
                            partial(mpris_set_position, track_id, position)
                        )
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Player"
                    and mpris_data[1] == "OpenUri"
                ):
                    mpris_play_url = mpris_data[2].unpack()[0]
                    execute_in_main_thread(
                        partial(itemClicked_event, mpris_play_url, mpris_play_url)
                    )
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Playlists"
                    and mpris_data[1] == "ActivatePlaylist"
                ):
                    execute_in_main_thread(
                        partial(mpris_select_playlist, mpris_data[2].unpack()[0])
                    )
                elif (
                    mpris_data[0] == "org.mpris.MediaPlayer2.Playlists"
                    and mpris_data[1] == "GetPlaylists"
                ):
                    (
                        _current_playlist_name,
                        _current_playlist,
                        playlists,
                    ) = get_playlists()
                    return GLib.Variant.new_tuple(GLib.Variant("a(oss)", playlists))
                elif (
                    mpris_data[0] == "org.freedesktop.DBus.Properties"
                    and mpris_data[1] == "Set"
                ):
                    mpris_data_params = mpris_data[2].unpack()
                    if (
                        mpris_data_params[0] == "org.mpris.MediaPlayer2"
                        and mpris_data_params[1] == "Fullscreen"
                    ):
                        if mpris_data_params[2]:
                            # Enable fullscreen
                            if not YukiData.fullscreen:
                                execute_in_main_thread(partial(mpv_fullscreen))
                        else:
                            # Disable fullscreen
                            if YukiData.fullscreen:
                                execute_in_main_thread(partial(mpv_fullscreen))
                    elif (
                        mpris_data_params[0] == "org.mpris.MediaPlayer2.Player"
                        and mpris_data_params[1] == "LoopStatus"
                    ):
                        # Not implemented
                        pass
                    elif (
                        mpris_data_params[0] == "org.mpris.MediaPlayer2.Player"
                        and mpris_data_params[1] == "Rate"
                    ):
                        execute_in_main_thread(
                            partial(set_playback_speed, mpris_data_params[2])
                        )
                    elif (
                        mpris_data_params[0] == "org.mpris.MediaPlayer2.Player"
                        and mpris_data_params[1] == "Shuffle"
                    ):
                        # Not implemented
                        pass
                    elif (
                        mpris_data_params[0] == "org.mpris.MediaPlayer2.Player"
                        and mpris_data_params[1] == "Volume"
                    ):
                        execute_in_main_thread(
                            partial(mpris_set_volume, mpris_data_params[2])
                        )
                # Always responding None, even if unknown command called
                # to prevent freezing
                return None

            def get_mpris_metadata():
                if YukiData.playing_channel:
                    if YukiData.player.pause or YukiData.is_loading:
                        playback_status = "Paused"
                    else:
                        playback_status = "Playing"
                else:
                    playback_status = "Stopped"
                playing_url_hash = hashlib.sha512(
                    YukiData.playing_url.encode("utf-8")
                ).hexdigest()
                mpris_trackid = (
                    f"/page/codeberg/liya/yuki_iptv/Track/{playing_url_hash}"
                    if YukiData.playing_url
                    else "/page/codeberg/liya/yuki_iptv/Track/NoTrack"
                )
                artUrl = ""
                if YukiData.playing_channel in YukiData.array:
                    if "tvg-logo" in YukiData.array[YukiData.playing_channel]:
                        if YukiData.array[YukiData.playing_channel]["tvg-logo"]:
                            artUrl = YukiData.array[YukiData.playing_channel][
                                "tvg-logo"
                            ]
                # Position in microseconds
                player_position = (
                    YukiData.player.duration * 1000000
                    if YukiData.player.duration
                    else 0
                )
                return playback_status, mpris_trackid, artUrl, player_position

            def get_mpris_options():
                if (
                    YukiData.player
                    and YukiData.mpris_ready
                    and YukiData.mpris_running
                    and not YukiData.stopped
                ):
                    (
                        playback_status,
                        mpris_trackid,
                        artUrl,
                        player_position,
                    ) = get_mpris_metadata()
                    current_playlist_name, current_playlist, playlists = get_playlists()
                    return {
                        "org.mpris.MediaPlayer2": {
                            "CanQuit": GLib.Variant("b", True),
                            "Fullscreen": GLib.Variant("b", YukiData.fullscreen),
                            "CanSetFullscreen": GLib.Variant("b", True),
                            "CanRaise": GLib.Variant("b", True),
                            "HasTrackList": GLib.Variant("b", False),
                            "Identity": GLib.Variant("s", "yuki-iptv"),
                            "DesktopEntry": GLib.Variant("s", "yuki-iptv"),
                            "SupportedUriSchemes": GLib.Variant(
                                "as",
                                ("file", "http", "https", "rtp", "udp"),
                            ),
                            "SupportedMimeTypes": GLib.Variant(
                                "as",
                                (
                                    "audio/mpeg",
                                    "audio/x-mpeg",
                                    "video/mpeg",
                                    "video/x-mpeg",
                                    "video/x-mpeg-system",
                                    "video/mp4",
                                    "audio/mp4",
                                    "video/x-msvideo",
                                    "video/quicktime",
                                    "application/ogg",
                                    "application/x-ogg",
                                    "video/x-ms-asf",
                                    "video/x-ms-asf-plugin",
                                    "application/x-mplayer2",
                                    "video/x-ms-wmv",
                                    "video/x-google-vlc-plugin",
                                    "audio/x-wav",
                                    "audio/3gpp",
                                    "video/3gpp",
                                    "audio/3gpp2",
                                    "video/3gpp2",
                                    "video/x-flv",
                                    "video/x-matroska",
                                    "audio/x-matroska",
                                    "application/xspf+xml",
                                ),
                            ),
                        },
                        "org.mpris.MediaPlayer2.Player": {
                            "PlaybackStatus": GLib.Variant("s", playback_status),
                            "LoopStatus": GLib.Variant("s", "None"),
                            "Rate": GLib.Variant("d", YukiData.player.speed),
                            "Shuffle": GLib.Variant("b", False),
                            "Metadata": GLib.Variant(
                                "a{sv}",
                                {
                                    "mpris:trackid": GLib.Variant("o", mpris_trackid),
                                    "mpris:artUrl": GLib.Variant("s", artUrl),
                                    "mpris:length": GLib.Variant("x", player_position),
                                    "xesam:url": GLib.Variant(
                                        "s", YukiData.playing_url
                                    ),
                                    "xesam:title": GLib.Variant(
                                        "s", YukiData.playing_channel
                                    ),
                                },
                            ),
                            "Volume": GLib.Variant(
                                "d", float(YukiData.player.volume / 100)
                            ),
                            "Position": GLib.Variant(
                                "x",
                                YukiData.player.time_pos * 1000000
                                if YukiData.player.time_pos
                                else 0,
                            ),
                            "MinimumRate": GLib.Variant("d", 0.01),
                            "MaximumRate": GLib.Variant("d", 5.0),
                            "CanGoNext": GLib.Variant("b", True),
                            "CanGoPrevious": GLib.Variant("b", True),
                            "CanPlay": GLib.Variant("b", True),
                            "CanPause": GLib.Variant("b", True),
                            "CanSeek": GLib.Variant("b", True),
                            "CanControl": GLib.Variant("b", True),
                        },
                        "org.mpris.MediaPlayer2.Playlists": {
                            "PlaylistCount": GLib.Variant("u", len(playlists)),
                            "Orderings": GLib.Variant("as", ("UserDefined",)),
                            "ActivePlaylist": GLib.Variant(
                                "(b(oss))",
                                (
                                    True,
                                    GLib.Variant(
                                        "(oss)",
                                        current_playlist,
                                    ),
                                ),
                            ),
                        },
                    }
                else:
                    return {}

            def wait_until():
                while True:
                    if win.isVisible() or YukiData.stopped:
                        return True
                    else:
                        time.sleep(0.1)
                return False

            def mpris_loop_start():
                wait_until()
                if not YukiData.stopped:
                    try:
                        mpris_owner_bus_id = start_mpris(
                            os.getpid(), mpris_callback, get_mpris_options
                        )
                        YukiData.mpris_ready = True
                        YukiData.mpris_running = True
                        YukiData.mpris_loop.run()
                        Gio.bus_unown_name(mpris_owner_bus_id)
                    except Exception:
                        logger.warning("MPRIS loop error!")
                        logger.warning(traceback.format_exc())

            YukiData.mpris_loop = GLib.MainLoop()
            mpris_thread = threading.Thread(target=mpris_loop_start)
            mpris_thread.start()

            class MPRISEventHandler:
                def on_metadata(self):
                    if (
                        YukiData.player
                        and YukiData.mpris_ready
                        and YukiData.mpris_running
                        and not YukiData.stopped
                    ):
                        (
                            playback_status,
                            mpris_trackid,
                            artUrl,
                            player_position,
                        ) = get_mpris_metadata()
                        execute_in_main_thread(
                            partial(
                                emit_mpris_change,
                                "org.mpris.MediaPlayer2.Player",
                                {
                                    "PlaybackStatus": GLib.Variant(
                                        "s", playback_status
                                    ),
                                    "Rate": GLib.Variant("d", YukiData.player.speed),
                                    "Metadata": GLib.Variant(
                                        "a{sv}",
                                        {
                                            "mpris:trackid": GLib.Variant(
                                                "o", mpris_trackid
                                            ),
                                            "mpris:artUrl": GLib.Variant("s", artUrl),
                                            "mpris:length": GLib.Variant(
                                                "x", player_position
                                            ),
                                            "xesam:url": GLib.Variant(
                                                "s", YukiData.playing_url
                                            ),
                                            "xesam:title": GLib.Variant(
                                                "s", YukiData.playing_channel
                                            ),
                                        },
                                    ),
                                },
                            )
                        )

                def on_playpause(self):
                    if (
                        YukiData.player
                        and YukiData.mpris_ready
                        and YukiData.mpris_running
                        and not YukiData.stopped
                    ):
                        (
                            playback_status,
                            mpris_trackid,
                            artUrl,
                            player_position,
                        ) = get_mpris_metadata()
                        execute_in_main_thread(
                            partial(
                                emit_mpris_change,
                                "org.mpris.MediaPlayer2.Player",
                                {"PlaybackStatus": GLib.Variant("s", playback_status)},
                            )
                        )

                def on_volume(self):
                    if (
                        YukiData.player
                        and YukiData.mpris_ready
                        and YukiData.mpris_running
                        and not YukiData.stopped
                    ):
                        execute_in_main_thread(
                            partial(
                                emit_mpris_change,
                                "org.mpris.MediaPlayer2.Player",
                                {
                                    "Volume": GLib.Variant(
                                        "d", float(YukiData.player.volume / 100)
                                    )
                                },
                            )
                        )

                def on_fullscreen(self):
                    if (
                        YukiData.player
                        and YukiData.mpris_ready
                        and YukiData.mpris_running
                        and not YukiData.stopped
                    ):
                        execute_in_main_thread(
                            partial(
                                emit_mpris_change,
                                "org.mpris.MediaPlayer2",
                                {"Fullscreen": GLib.Variant("b", YukiData.fullscreen)},
                            )
                        )

            YukiData.event_handler = MPRISEventHandler()
        except Exception:
            logger.warning(traceback.format_exc())
            logger.warning("Failed to set up MPRIS!")

        def update_scheduler_programme():
            channel_list_2 = [channel_name for channel_name in YukiData.array_sorted]
            ch_choosed = YukiGUI.choosechannel_ch.currentText()
            YukiGUI.tvguide_sch.clear()
            if ch_choosed in channel_list_2:
                tvguide_got = re.sub(
                    "<[^<]+?>", "", update_tvguide(ch_choosed, True)
                ).split("!@#$%^^&*(")[2:]
                for tvguide_el in tvguide_got:
                    if tvguide_el:
                        YukiGUI.tvguide_sch.addItem(tvguide_el)

        def show_scheduler():
            if YukiGUI.scheduler_win.isVisible():
                YukiGUI.scheduler_win.hide()
            else:
                YukiGUI.choosechannel_ch.clear()
                channel_list = [channel_name for channel_name in YukiData.array_sorted]
                for channel1 in channel_list:
                    YukiGUI.choosechannel_ch.addItem(channel1)
                if YukiData.item_selected in channel_list:
                    YukiGUI.choosechannel_ch.setCurrentIndex(
                        channel_list.index(YukiData.item_selected)
                    )
                YukiGUI.choosechannel_ch.currentIndexChanged.connect(
                    update_scheduler_programme
                )
                update_scheduler_programme()
                move_window_to_center(YukiGUI.scheduler_win)
                YukiGUI.scheduler_win.show()

        def mpv_volume_set_custom():
            mpv_volume_set()

        YukiGUI.btn_playpause.clicked.connect(mpv_play)
        YukiGUI.btn_stop.clicked.connect(mpv_stop)
        YukiGUI.btn_fullscreen.clicked.connect(mpv_fullscreen)
        YukiGUI.btn_open_recordings_folder.clicked.connect(open_recording_folder_async)
        YukiGUI.btn_record.clicked.connect(do_record)
        YukiGUI.btn_show_scheduler.clicked.connect(show_scheduler)
        YukiGUI.btn_volume.clicked.connect(mpv_mute)
        YukiGUI.volume_slider.valueChanged.connect(mpv_volume_set_custom)
        YukiGUI.btn_screenshot.clicked.connect(do_screenshot)
        YukiGUI.btn_show_archive.clicked.connect(show_archive)
        YukiGUI.btn_multiepg.clicked.connect(show_multi_epg)
        YukiGUI.btn_tv_guide.clicked.connect(show_tvguide)
        YukiGUI.btn_prev_channel.clicked.connect(prev_channel)
        YukiGUI.btn_next_channel.clicked.connect(next_channel)

        dockWidget_controlPanel.setTitleBarWidget(QtWidgets.QWidget())
        dockWidget_controlPanel.setWidget(YukiGUI.controlpanel_dock_widget)
        dockWidget_controlPanel.setFloating(False)
        dockWidget_controlPanel.setFixedHeight(DOCKWIDGET_CONTROLPANEL_HEIGHT_HIGH)
        dockWidget_controlPanel.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        )
        win.addDockWidget(
            QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, dockWidget_controlPanel
        )

        YukiGUI.progress.hide()
        YukiGUI.start_label.hide()
        YukiGUI.stop_label.hide()
        dockWidget_controlPanel.setFixedHeight(DOCKWIDGET_CONTROLPANEL_HEIGHT_LOW)

        YukiData.state = QtWidgets.QLabel(win)
        YukiData.state.setStyleSheet("background-color: #a2a3a3;")
        YukiData.state.setFont(YukiGUI.font_12_bold)
        YukiData.state.setWordWrap(True)
        YukiData.state.move(50, 50)
        YukiData.state.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        YukiGUI.set_widget_opacity(YukiData.state, YukiGUI.DEFAULT_OPACITY)

        class Slider(QtWidgets.QSlider):
            def getRewindTime(self):
                s_start = None
                s_stop = None
                s_index = None
                if YukiData.archive_epg:
                    s_start = datetime.datetime.strptime(
                        YukiData.archive_epg[1], "%d.%m.%Y %H:%M:%S"
                    ).timestamp()
                    s_stop = datetime.datetime.strptime(
                        YukiData.archive_epg[2], "%d.%m.%Y %H:%M:%S"
                    ).timestamp()
                    s_index = YukiData.archive_epg[3]
                else:
                    if get_epg_url() and YukiData.playing_channel:
                        prog1 = None
                        epg_id = get_epg_id(YukiData.playing_channel)
                        if epg_id:
                            programmes = get_epg_programmes(epg_id)
                            if programmes:
                                prog1 = programmes
                        if prog1:
                            for pr in prog1:
                                if (
                                    time.time() > pr["start"]
                                    and time.time() < pr["stop"]
                                ):
                                    s_start = pr["start"]
                                    s_stop = (
                                        datetime.datetime.now().timestamp()
                                    )  # pr["stop"]
                                    s_index = prog1.index(pr)
                if not s_start:
                    return None
                return (
                    s_start + (self.value() / 100) * (s_stop - s_start),
                    s_stop,
                    s_index,
                )

            def mouseMoveEvent(self, event1):
                if YukiData.playing_channel:
                    rewind_time = self.getRewindTime()
                    if rewind_time:
                        QtWidgets.QToolTip.showText(
                            self.mapToGlobal(event1.pos()),
                            datetime.datetime.fromtimestamp(rewind_time[0]).strftime(
                                "%H:%M:%S"
                            ),
                        )
                super().mouseMoveEvent(event1)

            def doMouseReleaseEvent(self):
                if YukiData.playing_channel:
                    QtWidgets.QToolTip.hideText()
                    rewind_time = self.getRewindTime()
                    if rewind_time:
                        YukiData.rewind_value = self.value()
                        do_open_archive(
                            "#__rewind__#__archive__"
                            + urllib.parse.quote_plus(
                                json.dumps(
                                    [
                                        YukiData.playing_channel,
                                        datetime.datetime.fromtimestamp(
                                            rewind_time[0]
                                        ).strftime("%d.%m.%Y %H:%M:%S"),
                                        datetime.datetime.fromtimestamp(
                                            rewind_time[1]
                                        ).strftime("%d.%m.%Y %H:%M:%S"),
                                        rewind_time[2],
                                        True,
                                    ]
                                )
                            )
                        )

            def mouseReleaseEvent(self, event1):
                self.doMouseReleaseEvent()
                super().mouseReleaseEvent(event1)

        YukiGUI.create_rewind(Slider)

        def set_text_state(text="", is_previous=False):
            if is_previous:
                text = YukiData.previous_text
            else:
                YukiData.previous_text = text
            if YukiData.gl_is_static:
                br = "    "
                if not text or not YukiData.static_text:
                    br = ""
                text = YukiData.static_text + br + text
            win.update()
            YukiData.state.setText(text)

        def set_text_static(is_static):
            YukiData.static_text = ""
            YukiData.gl_is_static = is_static

        YukiData.state.setTextYuki = set_text_state
        YukiData.state.setStaticYuki = set_text_static
        YukiData.state.hide()

        def getUserAgent():
            try:
                userAgent2 = YukiData.player.user_agent
            except Exception:
                userAgent2 = default_user_agent
            return userAgent2

        def saveLastChannel():
            if YukiData.playing_url and playmode_selector.currentIndex() == 0:
                current_group_0 = 0
                if YukiData.combobox.currentIndex() != 0:
                    try:
                        current_group_0 = groups.index(
                            YukiData.array[YukiData.playing_channel]["tvg-group"]
                        )
                    except Exception:
                        pass
                current_channel_0 = 0
                try:
                    current_channel_0 = win.listWidget.currentRow()
                except Exception:
                    pass
                lastfile = open(
                    str(Path(LOCAL_DIR, "lastchannels.json")), "w", encoding="utf8"
                )
                lastfile.write(
                    json.dumps(
                        [
                            YukiData.playing_channel,
                            YukiData.playing_url,
                            getUserAgent(),
                            current_group_0,
                            current_channel_0,
                        ]
                    )
                )
                lastfile.close()
            else:
                if os.path.isfile(str(Path(LOCAL_DIR, "lastchannels.json"))):
                    os.remove(str(Path(LOCAL_DIR, "lastchannels.json")))

        def cur_win_width():
            w1_width = 0
            for app_scr in app.screens():
                w1_width += app_scr.size().width()
            return w1_width

        def cur_win_height():
            w1_height = 0
            for app_scr in app.screens():
                w1_height += app_scr.size().height()
            return w1_height

        def myExitHandler_before():
            try:
                for broken_logo in YukiData.broken_logos:
                    if os.path.isfile(broken_logo):
                        os.remove(broken_logo)
                channel_logos = os.listdir(Path(CACHE_DIR, "logo"))
                for channel_logo in channel_logos:
                    if os.path.isfile(
                        Path(CACHE_DIR, "logo", channel_logo)
                    ) and channel_logo.endswith(".png"):
                        os.remove(Path(CACHE_DIR, "logo", channel_logo))
                if YukiData.epg_pool:
                    try:
                        YukiData.epg_pool.close()
                        YukiData.epg_pool = None
                    except Exception:
                        pass
                uninhibit()
                if YukiData.comboboxIndex != -1:
                    write_option(
                        "comboboxindex",
                        {
                            "m3u": YukiData.settings["m3u"],
                            "index": YukiData.comboboxIndex,
                        },
                    )
                try:
                    if get_first_run():
                        write_option("vf_filters", get_active_vf_filters())
                except Exception:
                    pass
                try:
                    if not YukiData.first_start:
                        write_option(
                            "window",
                            {
                                "x": win.geometry().x(),
                                "y": win.geometry().y(),
                                "w": win.width(),
                                "h": win.height(),
                            },
                        )
                        if YukiData.settings["panelposition"] == 2:
                            write_option(
                                "separate_playlist",
                                {
                                    "x": dockWidget_playlist.geometry().x(),
                                    "y": dockWidget_playlist.geometry().y(),
                                    "w": dockWidget_playlist.width(),
                                    "h": dockWidget_playlist.height(),
                                },
                            )
                except Exception:
                    pass
                try:
                    write_option(
                        "compactstate",
                        {
                            "compact_mode": YukiData.compact_mode,
                            "playlist_hidden": YukiData.playlist_hidden,
                            "controlpanel_hidden": YukiData.controlpanel_hidden,
                        },
                    )
                except Exception:
                    pass
                try:
                    if YukiGUI.save_fullscreenPlaylistWidth:
                        write_option(
                            "fullscreen_playlist_width",
                            YukiGUI.save_fullscreenPlaylistWidth,
                        )
                    if YukiGUI.save_fullscreenPlaylistHeight:
                        write_option(
                            "fullscreen_playlist_height",
                            YukiGUI.save_fullscreenPlaylistHeight,
                        )
                except Exception:
                    pass
                try:
                    write_option("volume", int(YukiData.volume))
                except Exception:
                    pass
                save_player_tracks()
                saveLastChannel()
                stop_record()
                for rec_1 in sch_recordings:
                    do_stop_record(rec_1)
                if YukiData.mpris_loop:
                    YukiData.mpris_running = False
                    YukiData.mpris_loop.quit()
                YukiData.stopped = True
                if multiprocessing_manager:
                    multiprocessing_manager.shutdown()
                for process_3 in active_children():
                    try:
                        process_3.kill()
                    except Exception:
                        try:
                            process_3.terminate()
                        except Exception:
                            pass
            except Exception:
                logger.warning(traceback.format_exc())
            exit_handler()

        def myExitHandler():
            myExitHandler_before()
            if not YukiData.do_save_settings:
                sys.exit(0)

        def get_catchup_days(is_seconds=False):
            try:
                catchup_days1 = min(
                    max(
                        1,
                        max(
                            int(YukiData.array[xc1]["catchup-days"])
                            for xc1 in YukiData.array
                            if "catchup-days" in YukiData.array[xc1]
                        ),
                    ),
                    7,
                )
            except Exception:
                catchup_days1 = 7
            if is_seconds:
                catchup_days1 = 86400 * (catchup_days1 + 1)
            return catchup_days1

        logger.info(f"catchup-days = {get_catchup_days()}")

        def timer_channels_redraw():
            YukiData.ic += 0.1

            # redraw every 15 seconds
            if YukiData.ic > (
                14.9 if not YukiData.mp_manager_dict["logos_inprogress"] else 2.9
            ):
                YukiData.ic = 0
                execute_in_main_thread(partial(redraw_channels))
            YukiData.ic3 += 0.1

            if YukiData.ic3 > (
                14.9 if not YukiData.mp_manager_dict["logosmovie_inprogress"] else 2.9
            ):
                YukiData.ic3 = 0
                update_movie_icons()

        def thread_tvguide_update_start():
            YukiData.state.setStaticYuki(True)
            YukiData.state.show()
            YukiData.static_text = _("Updating TV guide...")
            YukiData.state.setTextYuki("")
            YukiData.time_stop = time.time() + 3

        def thread_tvguide_update_error():
            YukiData.static_text = ""
            YukiData.state.setStaticYuki(False)
            YukiData.state.show()
            YukiData.state.setTextYuki(_("TV guide update error!"))
            YukiData.time_stop = time.time() + 3

        def thread_tvguide_update_outdated():
            YukiData.static_text = ""
            YukiData.state.setStaticYuki(False)
            YukiData.state.show()
            YukiData.state.setTextYuki(_("EPG is outdated!"))
            YukiData.time_stop = time.time() + 3

        def thread_tvguide_update_end():
            YukiData.static_text = ""
            YukiData.state.setStaticYuki(False)
            YukiData.state.show()
            YukiData.state.setTextYuki(_("TV guide update done!"))
            YukiData.time_stop = time.time() + 0.5

        def timer_record():
            try:
                YukiData.ic1 += 0.1
                if YukiData.ic1 > 0.9:
                    YukiData.ic1 = 0
                    # executing every second
                    if YukiData.is_recording:
                        if not YukiData.recording_time:
                            YukiData.recording_time = time.time()
                        record_time = format_seconds(
                            time.time() - YukiData.recording_time
                        )
                        if os.path.isfile(YukiData.record_file):
                            record_size = convert_size(
                                os.path.getsize(YukiData.record_file)
                            )
                            YukiGUI.lbl2.setText(
                                "REC " + record_time + " - " + record_size
                            )
                        else:
                            YukiData.recording_time = time.time()
                            YukiGUI.lbl2.setText(_("Waiting for record"))
                win.update()
                if (time.time() > YukiData.time_stop) and YukiData.time_stop != 0:
                    YukiData.time_stop = 0
                    if not YukiData.gl_is_static:
                        YukiData.state.hide()
                        win.update()
                    else:
                        YukiData.state.setTextYuki("")
            except Exception:
                pass

        def do_reconnect_stream():
            if (YukiData.playing_channel and not YukiData.is_loading) and (
                YukiData.player.cache_buffering_state == 0
            ):
                logger.info("Reconnecting to stream")
                try:
                    doPlay(*YukiData.do_play_args)
                except Exception:
                    logger.warning("Failed reconnecting to stream - no known URL")
            YukiData.x_conn = None

        def check_connection():
            if YukiData.settings["autoreconnection"]:
                if YukiData.playing_group == 0:
                    if not YukiData.connprinted:
                        YukiData.connprinted = True
                        logger.info("Connection loss detector enabled")
                    try:
                        if (
                            YukiData.playing_channel and not YukiData.is_loading
                        ) and YukiData.player.cache_buffering_state == 0:
                            if not YukiData.x_conn:
                                logger.warning(
                                    "Connection to stream lost, waiting 5 secs..."
                                )
                                YukiData.x_conn = QtCore.QTimer()
                                YukiData.x_conn.timeout.connect(do_reconnect_stream)
                                YukiData.x_conn.start(5000)
                    except Exception:
                        logger.warning("Failed to set connection loss detector!")
            else:
                if not YukiData.connprinted:
                    YukiData.connprinted = True
                    logger.info("Connection loss detector disabled")

        def timer_check_tvguide_obsolete():
            try:
                if win.isVisible():
                    check_connection()
                    try:
                        if YukiData.player.video_bitrate:
                            bitrate_arr = [
                                _("bps") + " ",
                                _("kbps"),
                                _("Mbps"),
                                _("Gbps"),
                                _("Tbps"),
                            ]
                            video_bitrate = " - " + str(
                                format_bytes(YukiData.player.video_bitrate, bitrate_arr)
                            )
                        else:
                            video_bitrate = ""
                    except Exception:
                        video_bitrate = ""
                    try:
                        audio_codec = YukiData.player.audio_codec.split(" ")[0].strip()
                    except Exception:
                        audio_codec = "no audio"
                    try:
                        codec = YukiData.player.video_codec.split(" ")[0].strip()
                        width = YukiData.player.width
                        height = YukiData.player.height
                    except Exception:
                        codec = "png"
                        width = 800
                        height = 600
                    if YukiData.player.avsync:
                        avsync = str(round(YukiData.player.avsync, 2))
                        deavsync = round(YukiData.player.avsync, 2)
                        if deavsync < 0:
                            deavsync = deavsync * -1
                        if deavsync > 0.999:
                            avsync = f"<span style='color: #B58B00;'>{avsync}</span>"
                    else:
                        avsync = "0.0"
                    if (
                        not (codec.lower() == "png" and width == 800 and height == 600)
                    ) and (width and height):
                        if YukiData.settings["hidebitrateinfo"]:
                            YukiGUI.label_video_data.setText("")
                            YukiGUI.label_avsync.setText("")
                        else:
                            YukiGUI.label_video_data.setText(
                                f"  {width}x{height}"
                                f" - {codec} / {audio_codec}{video_bitrate} -"
                            )
                            YukiGUI.label_avsync.setText(f"A-V {avsync}")
                        if loading.text() == _("Loading..."):
                            hideLoading()
                    else:
                        YukiGUI.label_video_data.setText("")
                        YukiGUI.label_avsync.setText("")
                    YukiData.ic2 += 0.1
                    if YukiData.ic2 > 29.9:
                        YukiData.ic2 = 0
                        if (
                            get_epg_url()
                            and not YukiData.epg_pool_running
                            and not YukiData.epg_failed
                        ):
                            is_actual = True
                            if YukiData.epg_update_date != 0:
                                is_actual = (
                                    time.time() - YukiData.epg_update_date
                                ) < 86400  # 1 day
                            if not check_programmes_actual() or not is_actual:
                                logger.info("EPG is outdated, updating it...")
                                purge_epg_cache()
                                thread_epg_update_3 = threading.Thread(
                                    target=epg_update, daemon=True
                                )
                                thread_epg_update_3.start()
            except Exception:
                pass

        def timer_tvguide_progress():
            try:
                if not YukiData.thread_tvguide_progress_lock:
                    YukiData.thread_tvguide_progress_lock = True
                    try:
                        if YukiData.epg_pool_running:
                            if (
                                "epg_progress" in YukiData.mp_manager_dict
                                and YukiData.mp_manager_dict["epg_progress"]
                            ):
                                YukiData.static_text = YukiData.mp_manager_dict[
                                    "epg_progress"
                                ]
                                YukiData.state.setTextYuki(is_previous=True)
                    except Exception:
                        pass
                    YukiData.thread_tvguide_progress_lock = False
            except Exception:
                pass

        def timer_update_time():
            try:
                YukiGUI.scheduler_clock.setText(get_current_time())
            except Exception:
                pass

        def timer_osc():
            try:
                if win.isVisible():
                    if YukiData.playing_url:
                        try:
                            if not YukiData.force_turnoff_osc:
                                set_mpv_osc(True)
                            else:
                                set_mpv_osc(False)
                        except Exception:
                            pass
                    else:
                        try:
                            set_mpv_osc(False)
                        except Exception:
                            pass
            except Exception:
                pass

        dockWidget_playlist.installEventFilter(win)

        YukiData.prev_cursor = QtGui.QCursor.pos()

        def timer_cursor():
            show_cursor = False
            cursor_offset = (
                QtGui.QCursor.pos().x()
                - YukiData.prev_cursor.x()
                + QtGui.QCursor.pos().y()
                - YukiData.prev_cursor.y()
            )
            if cursor_offset < 0:
                cursor_offset = cursor_offset * -1
            if cursor_offset > 5:
                YukiData.prev_cursor = QtGui.QCursor.pos()
                if (time.time() - YukiData.last_cursor_moved) > 0.3:
                    YukiData.last_cursor_moved = time.time()
                    YukiData.last_cursor_time = time.time() + 1
                    show_cursor = True
            show_cursor_really = True
            if not show_cursor:
                show_cursor_really = time.time() < YukiData.last_cursor_time
            if YukiData.fullscreen:
                try:
                    if show_cursor_really:
                        win.container.unsetCursor()
                    else:
                        win.container.setCursor(QtCore.Qt.CursorShape.BlankCursor)
                except Exception:
                    pass
            else:
                try:
                    win.container.unsetCursor()
                except Exception:
                    pass

        class SizeGrip(QtWidgets.QSizeGrip):
            def mousePressEvent(self, event):
                YukiGUI.playlistFullscreenIsResized = True
                super().mousePressEvent(event)

            def mouseReleaseEvent(self, mouseEvent):
                YukiGUI.playlistFullscreenIsResized = False
                super().mouseReleaseEvent(mouseEvent)
                YukiGUI.fullscreenPlaylistWidth = YukiGUI.playlist_widget.width()
                YukiGUI.fullscreenPlaylistHeight = YukiGUI.playlist_widget.height()
                YukiGUI.save_fullscreenPlaylistWidth = YukiGUI.fullscreenPlaylistWidth
                YukiGUI.save_fullscreenPlaylistHeight = YukiGUI.fullscreenPlaylistHeight

        sizeGrip = SizeGrip(YukiGUI.playlist_widget)

        def show_playlist_fullscreen():
            if not YukiGUI.fullscreenPlaylistHeight:
                YukiGUI.fullscreenPlaylistHeight = win.height() - 50

            if YukiData.settings["panelposition"] in (0, 2):
                YukiGUI.playlist_widget.move(
                    win.mapToGlobal(
                        QtCore.QPoint(win.width() - YukiGUI.fullscreenPlaylistWidth, 0)
                    )
                )
            else:
                YukiGUI.playlist_widget.move(win.mapToGlobal(QtCore.QPoint(0, 0)))

            YukiGUI.playlist_widget.resize(
                YukiGUI.fullscreenPlaylistWidth, YukiGUI.fullscreenPlaylistHeight
            )

            if YukiData.settings["enabletransparency"]:
                YukiGUI.playlist_widget.setWindowOpacity(0.75)
            YukiGUI.playlist_widget.setWindowFlags(
                QtCore.Qt.WindowType.CustomizeWindowHint
                | QtCore.Qt.WindowType.FramelessWindowHint
                | QtCore.Qt.WindowType.X11BypassWindowManagerHint
            )
            YukiGUI.pl_layout.addWidget(YukiGUI.widget)
            YukiGUI.pl_layout.addWidget(
                sizeGrip,
                0,
                QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignLeft,
            )
            YukiGUI.playlist_widget.show()

        def hide_playlist_fullscreen():
            YukiGUI.pl_layout.removeWidget(YukiGUI.widget)
            YukiGUI.pl_layout.removeWidget(sizeGrip)
            dockWidget_playlist.setWidget(YukiGUI.widget)
            YukiGUI.playlist_widget.hide()

        def resizeandmove_controlpanel():
            lb2_width = 0
            YukiGUI.controlpanel_widget.setFixedWidth(
                win.screen().availableGeometry().width()
            )
            for lb2_wdg in YukiGUI.show_lbls_fullscreen:
                if (
                    YukiGUI.controlpanel_layout.indexOf(lb2_wdg) != -1
                    and lb2_wdg.isVisible()
                ):
                    lb2_width += lb2_wdg.width() + 10
            YukiGUI.controlpanel_widget.setFixedWidth(lb2_width + 30)
            p_3 = (
                win.container.frameGeometry().center()
                - QtCore.QRect(
                    QtCore.QPoint(), YukiGUI.controlpanel_widget.sizeHint()
                ).center()
            )
            YukiGUI.controlpanel_widget.move(
                win.mapToGlobal(QtCore.QPoint(p_3.x() - 100, win.height() - 100))
            )

        def show_controlpanel_fullscreen():
            if not YukiData.VOLUME_SLIDER_WIDTH:
                YukiData.VOLUME_SLIDER_WIDTH = YukiGUI.volume_slider.width()
            YukiGUI.volume_slider.setFixedWidth(YukiData.VOLUME_SLIDER_WIDTH)
            if YukiData.settings["enabletransparency"]:
                YukiGUI.controlpanel_widget.setWindowOpacity(0.75)
            if YukiGUI.channelfilter.usePopup:
                YukiGUI.controlpanel_widget.setWindowFlags(
                    QtCore.Qt.WindowType.CustomizeWindowHint
                    | QtCore.Qt.WindowType.FramelessWindowHint
                    | QtCore.Qt.WindowType.X11BypassWindowManagerHint
                    | QtCore.Qt.WindowType.Popup
                )
            else:
                YukiGUI.controlpanel_widget.setWindowFlags(
                    QtCore.Qt.WindowType.CustomizeWindowHint
                    | QtCore.Qt.WindowType.FramelessWindowHint
                    | QtCore.Qt.WindowType.X11BypassWindowManagerHint
                )
            YukiGUI.cp_layout.addWidget(YukiGUI.controlpanel_dock_widget)
            resizeandmove_controlpanel()
            YukiGUI.controlpanel_widget.show()
            resizeandmove_controlpanel()

        def hide_controlpanel_fullscreen():
            if YukiData.VOLUME_SLIDER_WIDTH:
                YukiGUI.volume_slider.setFixedWidth(YukiData.VOLUME_SLIDER_WIDTH)
            YukiGUI.cp_layout.removeWidget(YukiGUI.controlpanel_dock_widget)
            dockWidget_controlPanel.setWidget(YukiGUI.controlpanel_dock_widget)
            YukiGUI.controlpanel_widget.hide()
            YukiGUI.rewind.hide()

        def timer_afterrecord():
            try:
                cur_recording = False
                if not YukiGUI.lbl2.isVisible():
                    if "REC / " not in YukiGUI.lbl2.text():
                        cur_recording = is_ffmpeg_recording() is False
                    else:
                        cur_recording = is_recording_func() is not True
                    if cur_recording:
                        showLoading2()
                    else:
                        hideLoading2()
            except Exception:
                pass

        def timer_shortcuts():
            try:
                if not YukiData.fullscreen:
                    menubar_new_st = win.menuBar().isVisible()
                    if menubar_new_st != YukiData.menubar_state:
                        YukiData.menubar_state = menubar_new_st
                        if YukiData.menubar_state:
                            setShortcutState(False)
                        else:
                            setShortcutState(True)
            except Exception:
                pass

        def timer_mouse():
            try:
                if win.isVisible():
                    if (
                        YukiData.state.isVisible()
                        and YukiData.state.text().startswith(_("Volume"))
                        and not is_show_volume()
                    ):
                        YukiData.state.hide()
                    YukiGUI.label_volume.setText(f"{int(YukiData.player.volume)}%")
                    if YukiData.settings["panelposition"] != 2:
                        dockWidget_playlist.setFixedWidth(DOCKWIDGET_PLAYLIST_WIDTH)
                    if YukiData.fullscreen:
                        cur_pos = QtGui.QCursor.pos()
                        is_inside_window = (
                            (
                                cur_pos.x() > win.pos().x() - 1
                                and cur_pos.x() < (win.pos().x() + win.width())
                            )
                            and (
                                cur_pos.y() > win.pos().y() - 1
                                and cur_pos.y() < (win.pos().y() + win.height())
                            )
                            and (win.hasFocus() or YukiData.dockWidget_playlistVisible)
                        )

                        cursor_x = win.container.mapFromGlobal(QtGui.QCursor.pos()).x()
                        win_width = win.width()
                        if YukiData.settings["panelposition"] in (0, 2):
                            is_cursor_x = cursor_x > win_width - (
                                YukiGUI.fullscreenPlaylistWidth + 10
                            )
                        else:
                            is_cursor_x = cursor_x < (
                                YukiGUI.fullscreenPlaylistWidth + 10
                            )
                        if (
                            is_cursor_x and cursor_x < win_width and is_inside_window
                        ) or YukiGUI.playlistFullscreenIsResized:
                            if not YukiData.dockWidget_playlistVisible:
                                YukiData.dockWidget_playlistVisible = True
                                show_playlist_fullscreen()
                        else:
                            YukiData.dockWidget_playlistVisible = False
                            hide_playlist_fullscreen()

                        cursor_y = win.container.mapFromGlobal(QtGui.QCursor.pos()).y()
                        win_height = win.height()
                        is_cursor_y = cursor_y > win_height - (
                            dockWidget_controlPanel.height() + 250
                        )
                        if is_cursor_y and cursor_y < win_height and is_inside_window:
                            if not YukiData.dockWidget_controlPanelVisible:
                                YukiData.dockWidget_controlPanelVisible = True
                                show_controlpanel_fullscreen()
                        else:
                            YukiData.dockWidget_controlPanelVisible = False
                            hide_controlpanel_fullscreen()
                    if YukiData.settings["rewindenable"]:
                        cur_pos = QtGui.QCursor.pos()
                        is_inside_window = (
                            cur_pos.x() > win.pos().x() - 1
                            and cur_pos.x() < (win.pos().x() + win.width())
                        ) and (
                            cur_pos.y() > win.pos().y() - 1
                            and cur_pos.y() < (win.pos().y() + win.height())
                        )

                        cursor_y = win.container.mapFromGlobal(QtGui.QCursor.pos()).y()
                        win_height = win.height()
                        is_cursor_y = cursor_y > win_height - (
                            dockWidget_controlPanel.height() + 250
                        )
                        if (
                            is_cursor_y
                            and cursor_y < win_height
                            and is_inside_window
                            and YukiData.playing_channel
                            and YukiData.playing_channel in YukiData.array
                            and YukiData.current_prog1
                            and not YukiData.check_playlist_visible
                            and not YukiData.check_controlpanel_visible
                        ):
                            if not YukiData.rewindWidgetVisible:
                                YukiData.rewindWidgetVisible = True
                                win.resize_rewind()
                                YukiGUI.rewind.show()
                        else:
                            YukiData.rewindWidgetVisible = False
                            if YukiGUI.rewind.isVisible():
                                if YukiData.rewind_value:
                                    if (
                                        YukiData.rewind_value
                                        != YukiGUI.rewind_slider.value()
                                    ):
                                        YukiGUI.rewind_slider.doMouseReleaseEvent()
                                YukiGUI.rewind.hide()
            except Exception:
                pass

        def idle_show_hide_playlist():
            if not YukiData.fullscreen:
                if dockWidget_playlist.isVisible():
                    YukiData.playlist_hidden = True
                    dockWidget_playlist.hide()
                else:
                    YukiData.playlist_hidden = False
                    dockWidget_playlist.show()

        def show_hide_playlist():
            execute_in_main_thread(partial(idle_show_hide_playlist))

        def lowpanel_ch():
            if dockWidget_controlPanel.isVisible():
                YukiData.controlpanel_hidden = True
                dockWidget_controlPanel.hide()
            else:
                YukiData.controlpanel_hidden = False
                dockWidget_controlPanel.show()

        def key_quit():
            YukiGUI.settings_win.close()
            YukiGUI.shortcuts_win.close()
            YukiGUI.shortcuts_win_2.close()
            win.close()
            YukiGUI.help_win.close()
            YukiGUI.streaminfo_win.close()
            YukiGUI.license_win.close()
            myExitHandler()
            app.quit()

        def dockwidget_controlpanel_resize_timer():
            try:
                if YukiGUI.start_label.text() and YukiGUI.start_label.isVisible():
                    if (
                        dockWidget_controlPanel.height()
                        != DOCKWIDGET_CONTROLPANEL_HEIGHT_HIGH
                    ):
                        dockWidget_controlPanel.setFixedHeight(
                            DOCKWIDGET_CONTROLPANEL_HEIGHT_HIGH
                        )
                else:
                    if (
                        dockWidget_controlPanel.height()
                        != DOCKWIDGET_CONTROLPANEL_HEIGHT_LOW
                    ):
                        dockWidget_controlPanel.setFixedHeight(
                            DOCKWIDGET_CONTROLPANEL_HEIGHT_LOW
                        )
            except Exception:
                pass

        def set_playback_speed(spd):
            try:
                logger.info(f"Set speed to {spd}")
                YukiData.player.speed = spd
                try:
                    YukiData.event_handler.on_metadata()
                except Exception:
                    pass
            except Exception:
                logger.warning("set_playback_speed failed")

        def mpv_seek(secs):
            try:
                if YukiData.playing_channel:
                    logger.info(f"Seeking to {secs} seconds")
                    YukiData.player.command("seek", secs)
            except Exception:
                logger.warning("mpv_seek failed")

        def mpv_frame_step():
            logger.info("frame-step")
            YukiData.player.command("frame-step")

        def mpv_frame_back_step():
            logger.info("frame-back-step")
            YukiData.player.command("frame-back-step")

        funcs = {
            "show_sort": show_sort,
            "key_t": show_hide_playlist,
            "esc_handler": esc_handler,
            "mpv_fullscreen": mpv_fullscreen,
            "mpv_fullscreen_2": mpv_fullscreen,
            "open_stream_info": open_stream_info,
            "mpv_mute": mpv_mute,
            "key_quit": key_quit,
            "mpv_play": mpv_play,
            "mpv_stop": mpv_stop,
            "do_screenshot": do_screenshot,
            "show_tvguide": show_tvguide,
            "do_record": do_record,
            "prev_channel": prev_channel,
            "next_channel": next_channel,
            "(lambda: my_up_binding())": (lambda: my_up_binding_execute()),
            "(lambda: my_down_binding())": (lambda: my_down_binding_execute()),
            "show_timeshift": show_archive,
            "show_scheduler": show_scheduler,
            "showhideeverything": showhideeverything,
            "show_settings": show_settings,
            "(lambda: set_playback_speed(1.00))": (lambda: set_playback_speed(1.00)),
            "app.quit": app.quit,
            "show_playlists": show_playlists,
            "reload_playlist": reload_playlist,
            "force_update_epg": force_update_epg_act,
            "main_channel_settings": main_channel_settings,
            "show_m3u_editor": show_playlist_editor,
            "my_down_binding_execute": my_down_binding_execute,
            "my_up_binding_execute": my_up_binding_execute,
            "(lambda: mpv_seek(-10))": (lambda: mpv_seek(-10)),
            "(lambda: mpv_seek(10))": (lambda: mpv_seek(10)),
            "(lambda: mpv_seek(-60))": (lambda: mpv_seek(-60)),
            "(lambda: mpv_seek(60))": (lambda: mpv_seek(60)),
            "(lambda: mpv_seek(-600))": (lambda: mpv_seek(-600)),
            "(lambda: mpv_seek(600))": (lambda: mpv_seek(600)),
            "lowpanel_ch_1": lowpanel_ch_1,
            "show_tvguide_2": show_tvguide_2,
            "show_multi_epg": show_multi_epg,
            "do_record_1_INTERNAL": do_record,
            "mpv_mute_1_INTERNAL": mpv_mute,
            "mpv_play_1_INTERNAL": mpv_play,
            "mpv_play_2_INTERNAL": mpv_play,
            "mpv_play_3_INTERNAL": mpv_play,
            "mpv_play_4_INTERNAL": mpv_play,
            "mpv_stop_1_INTERNAL": mpv_stop,
            "mpv_stop_2_INTERNAL": mpv_stop,
            "next_channel_1_INTERNAL": next_channel,
            "prev_channel_1_INTERNAL": prev_channel,
            "(lambda: my_up_binding())_INTERNAL": (lambda: my_up_binding_execute()),
            "(lambda: my_down_binding())_INTERNAL": (lambda: my_down_binding_execute()),
            "mpv_frame_step": mpv_frame_step,
            "mpv_frame_back_step": mpv_frame_back_step,
        }

        if os.path.isfile(str(Path(LOCAL_DIR, "hotkeys.json"))):
            try:
                with open(
                    str(Path(LOCAL_DIR, "hotkeys.json")), encoding="utf8"
                ) as hotkeys_file_tmp:
                    hotkeys_tmp = json.loads(hotkeys_file_tmp.read())[
                        "current_profile"
                    ]["keys"]
                    YukiData.main_keybinds = hotkeys_tmp
                    logger.info("hotkeys.json found, using it as hotkey settings")
            except Exception:
                logger.warning("failed to read hotkeys.json, using default shortcuts")
                YukiData.main_keybinds = main_keybinds_default.copy()
        else:
            logger.info("No hotkeys.json found, using default hotkeys")
            YukiData.main_keybinds = main_keybinds_default.copy()

        seq = get_seq()

        def setShortcutState(st1):
            YukiData.shortcuts_state = st1
            for shortcut_arr in shortcuts:
                for shortcut in shortcuts[shortcut_arr]:
                    if shortcut.key() in seq:
                        shortcut.setEnabled(st1)

        def reload_keybinds():
            for shortcut_1 in shortcuts:
                if not shortcut_1.endswith("_INTERNAL"):
                    sc_new_keybind = QtGui.QKeySequence(get_keybind(shortcut_1))
                    for shortcut_2 in shortcuts[shortcut_1]:
                        shortcut_2.setKey(sc_new_keybind)
            reload_menubar_shortcuts()

        all_keybinds = YukiData.main_keybinds.copy()
        all_keybinds.update(main_keybinds_internal)
        for kbd in all_keybinds:
            if kbd in funcs:
                shortcuts[kbd] = [
                    # Main window
                    QtGui.QShortcut(
                        QtGui.QKeySequence(all_keybinds[kbd]), win, activated=funcs[kbd]
                    ),
                    # Control panel widget
                    QtGui.QShortcut(
                        QtGui.QKeySequence(all_keybinds[kbd]),
                        YukiGUI.controlpanel_widget,
                        activated=funcs[kbd],
                    ),
                    # Playlist widget
                    QtGui.QShortcut(
                        QtGui.QKeySequence(all_keybinds[kbd]),
                        YukiGUI.playlist_widget,
                        activated=funcs[kbd],
                    ),
                ]
            else:
                logger.warning(f"Unknown keybind {kbd}!")
        all_keybinds = False

        setShortcutState(False)

        app.aboutToQuit.connect(myExitHandler)

        vol_remembered = 100
        volume_option = read_option("volume")
        if volume_option is not None:
            vol_remembered = int(volume_option)
            YukiData.volume = vol_remembered

        def restore_compact_state():
            try:
                compactstate = read_option("compactstate")
                if compactstate:
                    if compactstate["compact_mode"]:
                        showhideeverything()
                    else:
                        if compactstate["playlist_hidden"]:
                            show_hide_playlist()
                        if compactstate["controlpanel_hidden"]:
                            lowpanel_ch()
            except Exception:
                pass

        def epg_update():
            if get_epg_url():
                if YukiData.epg_pool_running:
                    logger.info("EPG already updating")
                else:
                    if YukiData.first_boot:
                        YukiData.first_boot = False
                        if YukiData.settings["donotupdateepg"]:
                            logger.info("EPG update at boot disabled")
                            return

                    YukiData.epg_update_date = time.time()
                    YukiData.epg_pool_running = True
                    execute_in_main_thread(partial(thread_tvguide_update_start))

                    YukiData.epg_pool = get_context("spawn").Pool(1)
                    (
                        epg_failed,
                        epg_outdated,
                        YukiData.epg_array,
                    ) = YukiData.epg_pool.apply(
                        epg_worker,
                        (
                            get_epg_url(),
                            YukiData.settings,
                            YukiData.mp_manager_dict,
                        ),
                    )

                    YukiData.epg_pool.close()
                    YukiData.epg_pool = None

                    if epg_outdated:
                        execute_in_main_thread(partial(thread_tvguide_update_outdated))
                    elif epg_failed:
                        execute_in_main_thread(partial(thread_tvguide_update_error))
                    else:
                        execute_in_main_thread(partial(thread_tvguide_update_end))
                    YukiData.epg_failed = epg_outdated or epg_failed
                    YukiData.epg_pool_running = False

                    execute_in_main_thread(partial(redraw_channels))

        if YukiData.settings["m3u"] and m3u_exists:
            show_window(win)
            init_mpv_player()
            try:
                combobox_index1 = read_option("comboboxindex")
                if combobox_index1:
                    if combobox_index1["m3u"] == YukiData.settings["m3u"]:
                        if combobox_index1["index"] < YukiData.combobox.count():
                            YukiData.combobox.setCurrentIndex(combobox_index1["index"])
            except Exception:
                pass

            register()

            def after_mpv_init():
                if YukiData.needs_resize:
                    logger.debug("Fix window size")
                    win.resize(WINDOW_SIZE[0], WINDOW_SIZE[1])
                    move_window_to_center(win)
                if not playLastChannel():
                    logger.info("Show splash")
                    mpv_override_play(str(Path(YukiGUI.icons_folder, "main.png")))
                    YukiData.player.pause = True
                else:
                    logger.info("Playing last channel")
                restore_compact_state()

            after_mpv_init()

            YukiGUI.fullscreenPlaylistWidth = read_option("fullscreen_playlist_width")
            YukiGUI.fullscreenPlaylistHeight = read_option("fullscreen_playlist_height")

            if not YukiGUI.fullscreenPlaylistWidth:
                YukiGUI.fullscreenPlaylistWidth = DOCKWIDGET_PLAYLIST_WIDTH

            timers_array = {}
            timers = {
                timer_shortcuts: 25,
                timer_mouse: 50,
                timer_cursor: 50,
                timer_channels_redraw: 100,
                timer_record: 100,
                timer_osc: 100,
                timer_check_tvguide_obsolete: 100,
                timer_tvguide_progress: 100,
                timer_update_time: 1000,
                timer_logos_update: 1000,
                record_timer: 1000,
                record_timer_2: 1000,
                timer_afterrecord: 50,
                timer_bitrate: 5000,
                dockwidget_controlpanel_resize_timer: 50,
            }
            for timer in timers:
                timers_array[timer] = QtCore.QTimer()
                timers_array[timer].timeout.connect(timer)
                timers_array[timer].start(timers[timer])

            thread_epg_update_1 = threading.Thread(target=epg_update, daemon=True)
            thread_epg_update_1.start()
        else:
            YukiData.first_start = True
            show_playlists()
            move_window_to_center(gui_playlists_data.playlists_win)
            gui_playlists_data.playlists_win.show()

        app_exit_code = app.exec()
        if YukiData.do_save_settings:
            start_args = sys.argv
            if "python" not in sys.executable:
                start_args.pop(0)
            subprocess.Popen([sys.executable] + start_args)
        sys.exit(app_exit_code)
    except Exception:
        show_exception(traceback.format_exc())
        try:
            myExitHandler_before()
        except Exception:
            pass
        try:
            app.quit()
        except Exception:
            pass
        for process_4 in active_children():
            try:
                process_4.kill()
            except Exception:
                try:
                    process_4.terminate()
                except Exception:
                    pass
        kill_process_childs(os.getpid())
        sys.exit(1)
