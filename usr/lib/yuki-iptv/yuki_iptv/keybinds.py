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
from PyQt6 import QtCore
from yuki_iptv.i18n import _, ngettext

main_keybinds_internal = {
    "do_record_1_INTERNAL": QtCore.Qt.Key.Key_MediaRecord,
    "mpv_mute_1_INTERNAL": QtCore.Qt.Key.Key_VolumeMute,
    "mpv_play_1_INTERNAL": QtCore.Qt.Key.Key_MediaTogglePlayPause,
    "mpv_play_2_INTERNAL": QtCore.Qt.Key.Key_MediaPlay,
    "mpv_play_3_INTERNAL": QtCore.Qt.Key.Key_MediaPause,
    "mpv_play_4_INTERNAL": QtCore.Qt.Key.Key_Play,
    "mpv_stop_1_INTERNAL": QtCore.Qt.Key.Key_Stop,
    "mpv_stop_2_INTERNAL": QtCore.Qt.Key.Key_MediaStop,
    "next_channel_1_INTERNAL": QtCore.Qt.Key.Key_MediaNext,
    "prev_channel_1_INTERNAL": QtCore.Qt.Key.Key_MediaPrevious,
    "(lambda: my_down_binding())_INTERNAL": QtCore.Qt.Key.Key_VolumeDown,
    "(lambda: my_up_binding())_INTERNAL": QtCore.Qt.Key.Key_VolumeUp,
}

main_keybinds_default = {
    "mpv_play": QtCore.Qt.Key.Key_Space,
    "mpv_stop": QtCore.Qt.Key.Key_S,
    "mpv_mute": QtCore.Qt.Key.Key_M,
    "my_down_binding_execute": QtCore.Qt.Key.Key_9,
    "my_up_binding_execute": QtCore.Qt.Key.Key_0,
    "prev_channel": QtCore.Qt.Key.Key_B,
    "next_channel": QtCore.Qt.Key.Key_N,
    "key_quit": QtCore.Qt.Key.Key_Q,
    "app.quit": "Ctrl+Q",
    "do_record": QtCore.Qt.Key.Key_R,
    "do_screenshot": QtCore.Qt.Key.Key_H,
    "esc_handler": QtCore.Qt.Key.Key_Escape,
    "force_update_epg": "Ctrl+U",
    "key_t": QtCore.Qt.Key.Key_T,
    "lowpanel_ch_1": QtCore.Qt.Key.Key_P,
    "main_channel_settings": "Ctrl+S",
    "mpv_fullscreen": QtCore.Qt.Key.Key_F,
    "mpv_fullscreen_2": QtCore.Qt.Key.Key_F11,
    "open_stream_info": QtCore.Qt.Key.Key_F2,
    "show_m3u_editor": "Ctrl+E",
    "show_playlists": "Ctrl+O",
    "reload_playlist": "Ctrl+R",
    "show_scheduler": QtCore.Qt.Key.Key_D,
    "show_settings": "Ctrl+P",
    "show_sort": QtCore.Qt.Key.Key_I,
    "show_timeshift": QtCore.Qt.Key.Key_E,
    "show_tvguide": QtCore.Qt.Key.Key_G,
    "showhideeverything": "Ctrl+C",
    "show_tvguide_2": QtCore.Qt.Key.Key_J,
    "(lambda: mpv_seek(-10))": QtCore.Qt.Key.Key_Left,
    "(lambda: mpv_seek(-60))": QtCore.Qt.KeyboardModifier.ControlModifier
    | QtCore.Qt.Key.Key_Down,
    "(lambda: mpv_seek(-600))": QtCore.Qt.Key.Key_PageDown,
    "(lambda: mpv_seek(10))": QtCore.Qt.Key.Key_Right,
    "(lambda: mpv_seek(60))": QtCore.Qt.KeyboardModifier.ControlModifier
    | QtCore.Qt.Key.Key_Up,
    "(lambda: mpv_seek(600))": QtCore.Qt.Key.Key_PageUp,
    "(lambda: set_playback_speed(1.00))": QtCore.Qt.Key.Key_Backspace,
    "mpv_frame_step": QtCore.Qt.Key.Key_Period,
    "mpv_frame_back_step": QtCore.Qt.Key.Key_Comma,
    "show_multi_epg": QtCore.Qt.Key.Key_U,
}

main_keybinds_translations = {
    "(lambda: mpv_seek(-10))": ngettext("-%d second", "-%d seconds", 10) % 10,
    "(lambda: mpv_seek(-60))": ngettext("-%d minute", "-%d minutes", 1) % 1,
    "(lambda: mpv_seek(-600))": ngettext("-%d minute", "-%d minutes", 10) % 10,
    "(lambda: mpv_seek(10))": ngettext("+%d second", "+%d seconds", 10) % 10,
    "(lambda: mpv_seek(60))": ngettext("+%d minute", "+%d minutes", 1) % 1,
    "(lambda: mpv_seek(600))": ngettext("+%d minute", "+%d minutes", 10) % 10,
    "(lambda: my_down_binding())": _("V&olume -").replace("&", ""),
    "(lambda: my_up_binding())": _("Vo&lume +").replace("&", ""),
    "(lambda: set_playback_speed(1.00))": _("&Normal speed").replace("&", ""),
    "app.quit": _("Quit the program") + " (2)",
    "do_record": _("Record"),
    "do_screenshot": _("Screenshot").capitalize(),
    "esc_handler": _("Exit fullscreen"),
    "force_update_epg": _("&Update TV guide").replace("&", ""),
    "key_quit": _("Quit the program"),
    "key_t": _("Show/hide playlist"),
    "lowpanel_ch_1": _("Show/hide controls panel"),
    "main_channel_settings": _("&Video settings").replace("&", ""),
    "mpv_fullscreen": _("&Fullscreen").replace("&", ""),
    "mpv_fullscreen_2": _("&Fullscreen").replace("&", "") + " (2)",
    "mpv_mute": _("&Mute audio").replace("&", ""),
    "mpv_play": _("&Play / Pause").replace("&", ""),
    "mpv_stop": _("&Stop").replace("&", ""),
    "my_down_binding_execute": _("V&olume -").replace("&", ""),
    "my_up_binding_execute": _("Vo&lume +").replace("&", ""),
    "next_channel": _("&Next").replace("&", ""),
    "open_stream_info": _("Stream Information"),
    "prev_channel": _("&Previous").replace("&", ""),
    "show_m3u_editor": _("P&laylist editor").replace("&", ""),
    "show_playlists": _("&Playlists").replace("&", ""),
    "reload_playlist": _("&Update current playlist").replace("&", ""),
    "show_scheduler": _("Scheduler"),
    "show_settings": _("Settings"),
    "show_sort": _("Channel sort"),
    "show_timeshift": _("Archive"),
    "show_tvguide": _("TV guide"),
    "showhideeverything": _("&Compact mode").replace("&", ""),
    "show_tvguide_2": _("TV guide for all channels"),
    "mpv_frame_step": _("&Frame step").replace("&", ""),
    "mpv_frame_back_step": _("Fra&me back step").replace("&", ""),
    "show_multi_epg": _("Multi-EPG"),
}
