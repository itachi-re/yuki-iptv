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
from PyQt6 import QtCore
from yuki_iptv.i18n import _
from yuki_iptv.settings import parse_settings

logger = logging.getLogger(__name__)


class YukiData:
    ffmpeg_proc = None
    ffmpeg_processes = None
    show_record_exception = None


def is_ffmpeg_recording():
    ret = -2
    if YukiData.ffmpeg_proc:
        if YukiData.ffmpeg_proc.processId() == 0:
            YukiData.ffmpeg_proc = None
            ret = True
        else:
            ret = False
    return ret


def exit_handler(process, exit_code, _exit_status):
    is_killed = False
    try:
        is_killed = process._yuki_killed
    except Exception:
        pass
    if not is_killed:
        logger.warning("ffmpeg process crashed")
        if YukiData.show_record_exception:
            standard_output = process.readAllStandardOutput()
            try:
                standard_output = bytes(standard_output).decode("utf-8")
                standard_output = "\n".join(standard_output.split("\n")[-15:])
            except Exception:
                pass
            standard_error = process.readAllStandardError()
            try:
                standard_error = bytes(standard_error).decode("utf-8")
                standard_error = "\n".join(standard_error.split("\n")[-15:])
            except Exception:
                pass
            YukiData.show_record_exception(
                _("ffmpeg crashed!") + "\n"
                "" + _("exit code:") + " " + str(exit_code) + ""
                "\nstdout:\n" + str(standard_output) + ""
                "\nstderr:\n" + str(standard_error)
            )


def record(
    input_url,
    out_file,
    channel_name,
    http_referer,
    get_ua_ref_for_channel,
    is_return=False,
):
    settings, settings_loaded = parse_settings()
    if http_referer == "Referer: ":
        http_referer = ""
    useragent_ref, referer_ref = get_ua_ref_for_channel(channel_name)
    user_agent = useragent_ref
    origin_add = ""
    if referer_ref:
        http_referer = f"Referer: {referer_ref}"
        originURL = ""
        if referer_ref.endswith("/"):
            originURL = referer_ref[:-1]
        if originURL:
            origin_add = "Origin: " + originURL + "\r\n"
    logger.info(f"Using user agent '{user_agent}' for record channel '{channel_name}'")
    logger.info(f"HTTP headers: '{http_referer}'")
    if input_url.startswith("http://") or input_url.startswith("https://"):
        arr = [
            "-nostats",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-user_agent",
            user_agent,
            "-headers",
            http_referer + "\r\n" + origin_add,
            "-i",
            input_url,
            "-map",
            "-0:s?",
            "-sn",
            "-map",
            "-0:d?",
            "-map",
            "-0:t?",
            "-codec",
            "copy",
            "-max_muxing_queue_size",
            "4096",
            out_file,
        ]
    else:
        arr = [
            "-nostats",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-i",
            input_url,
            "-map",
            "-0:s?",
            "-sn",
            "-map",
            "-0:d?",
            "-map",
            "-0:t?",
            "-codec",
            "copy",
            "-max_muxing_queue_size",
            "4096",
            out_file,
        ]
    if not is_return:
        YukiData.ffmpeg_proc = QtCore.QProcess()
        YukiData.ffmpeg_proc.start("ffmpeg", arr)
        YukiData.ffmpeg_proc.finished.connect(
            lambda exit_code, exit_status: exit_handler(
                YukiData.ffmpeg_proc, exit_code, exit_status
            )
        )
    else:
        ffmpeg_ret_proc = QtCore.QProcess()
        ffmpeg_ret_proc.start("ffmpeg", arr)
        ffmpeg_ret_proc.finished.connect(
            lambda exit_code, exit_status: exit_handler(
                ffmpeg_ret_proc, exit_code, exit_status
            )
        )
        return ffmpeg_ret_proc


def terminate_record_process(proc):
    proc._yuki_killed = True
    proc.kill()


def stop_record():
    if YukiData.ffmpeg_proc:
        terminate_record_process(YukiData.ffmpeg_proc)


def init_record(show_exception, ffmpeg_processes):
    YukiData.show_record_exception = show_exception
    YukiData.ffmpeg_processes = ffmpeg_processes
