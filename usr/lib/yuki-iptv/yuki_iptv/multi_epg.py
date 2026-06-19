#
# Copyright (c) 2024, 2025 liya <liyaliya@tutamail.com>
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
import datetime
import traceback
from PyQt6 import QtCore, QtWidgets
from yuki_iptv.i18n import _
from yuki_iptv.misc import YukiData
from yuki_iptv.qt_exception import show_exception


class MultiEPGWindow(QtWidgets.QMainWindow):
    min_cell_width = 50
    cell_width = 150
    cell_width_step = 50
    cell_height = 40
    fixed_cell_width = 150
    footer_height = 125
    button_width = 24

    channels = []

    columns = 24  # hours in a day
    date = datetime.datetime.now()
    cell_current_time = None
    current_cells = []
    is_first = True
    page = 1
    bg_color = "#a8a8a8"

    def __init__(self):
        super().__init__()
        try:
            self.widget = QtWidgets.QWidget()
            self.layout = QtWidgets.QVBoxLayout()
            self.layout.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft
            )
            self.widget.setLayout(self.layout)
            self.setCentralWidget(self.widget)

            self.header_widget = QtWidgets.QWidget()
            self.header_layout = QtWidgets.QHBoxLayout()
            self.header_widget.setLayout(self.header_layout)
            self.layout.addWidget(self.header_widget)

            self.duration_label = QtWidgets.QLabel()
            globals()["_multiepg_duration_label"] = self.duration_label
            self.name_label = QtWidgets.QLabel()
            globals()["_multiepg_name_label"] = self.name_label
            self.desc_label = QtWidgets.QLabel()
            globals()["_multiepg_desc_label"] = self.desc_label
            self.desc_label.setWordWrap(True)

            self.duration_name_widget = QtWidgets.QWidget()
            self.duration_name_layout = QtWidgets.QHBoxLayout()
            self.duration_name_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            self.duration_name_layout.addWidget(self.duration_label)
            self.duration_name_layout.addWidget(self.name_label)
            self.duration_name_widget.setLayout(self.duration_name_layout)

            self.footer_widget = QtWidgets.QWidget(self)
            self.footer_layout = QtWidgets.QVBoxLayout()
            self.footer_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            self.footer_layout.setContentsMargins(0, 0, 0, 0)
            self.footer_layout.setSpacing(0)
            self.footer_layout.addWidget(self.duration_name_widget)
            self.footer_layout.addWidget(self.desc_label)
            self.footer_widget.setLayout(self.footer_layout)

            self.prev_button = QtWidgets.QPushButton("<")
            self.prev_button.setToolTip(_("Previous day"))
            self.prev_button.setMaximumWidth(self.button_width)
            self.prev_button.clicked.connect(self.prev_day)

            self.next_button = QtWidgets.QPushButton(">")
            self.next_button.setToolTip(_("Next day"))
            self.next_button.setMaximumWidth(self.button_width)
            self.next_button.clicked.connect(self.next_day)

            self.day_label = QtWidgets.QLabel()

            self.header_layout.addWidget(self.prev_button)
            self.header_layout.addWidget(self.next_button)
            self.header_layout.addWidget(self.day_label)

            self.increase_size_button = QtWidgets.QPushButton("+")
            self.increase_size_button.setMaximumWidth(self.button_width)
            self.increase_size_button.clicked.connect(self.increase_size)

            self.decrease_size_button = QtWidgets.QPushButton("-")
            self.decrease_size_button.setMaximumWidth(self.button_width)
            self.decrease_size_button.clicked.connect(self.decrease_size)

            self.previous_channels_button = QtWidgets.QPushButton(
                _("Previous channels")
            )
            self.previous_channels_button.clicked.connect(self.previous_channels)
            self.next_channels_button = QtWidgets.QPushButton(_("Next channels"))
            self.next_channels_button.clicked.connect(self.next_channels)

            self.groups_label = QtWidgets.QLabel("{}:".format(_("Group")))
            self.groups_combobox = QtWidgets.QComboBox()
            self.groups_combobox.currentIndexChanged.connect(self.set_group)

            self.header_layout.addStretch(1000000)  # TODO: find better solution
            self.header_layout.addWidget(self.increase_size_button)
            self.header_layout.addWidget(self.decrease_size_button)
            self.header_layout.addWidget(self.groups_label)
            self.header_layout.addWidget(self.groups_combobox)
            self.header_layout.addWidget(self.previous_channels_button)
            self.header_layout.addWidget(self.next_channels_button)

            self.fixed_column = QtWidgets.QWidget(self)
            self.channel_header_label = QtWidgets.QLabel(
                _("Channel"), self.fixed_column
            )
            self.channel_header_label.move(0, 0)
            self.channel_header_label.resize(self.fixed_cell_width, self.cell_height)

            class HorizontalScrollOnWheel(QtWidgets.QScrollArea):
                def wheelEvent(self, event):
                    delta = event.angleDelta().y()
                    if delta != 0:
                        h_scroll_bar = self.horizontalScrollBar()
                        h_scroll_bar.setValue(h_scroll_bar.value() - delta)

                    event.accept()

            self.scroll_area = HorizontalScrollOnWheel(self)
            self.scroll_area.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            self.update_scrollarea_size()
            self.table_widget = QtWidgets.QWidget()
            self.scroll_area.setWidget(self.table_widget)
            self.scroll_area.setWidgetResizable(True)
            self.layout = QtWidgets.QVBoxLayout(self.table_widget)
            self.layout.setSpacing(0)

            self.move_footer()
        except Exception:
            show_exception(traceback.format_exc())

    def previous_channels(self):
        try:
            self.page -= 1
            self.page = max(1, self.page)
            self.set_channels_page()
            self.create_program_cells()
        except Exception:
            show_exception(traceback.format_exc())

    def next_channels(self):
        try:
            self.page += 1
            self.set_channels_page()
            self.create_program_cells()
        except Exception:
            show_exception(traceback.format_exc())

    def set_group(self):
        try:
            self.page = 1
            self.set_channels_page()
            self.create_program_cells()
        except Exception:
            show_exception(traceback.format_exc())

    def first(self):
        try:
            self.set_channels_page()
            self.create_program_cells()

            if self.is_first:
                self.is_first = False

                self.date = datetime.datetime.now()
                self.set_day_label()

                self.update_time()

                self.timer = QtCore.QTimer(self)
                self.timer.setInterval(1000)
                self.timer.timeout.connect(self.update_time)
                self.timer.start()

                self.groups_combobox.clear()
                for group_sorted in YukiData.groups_sorted:
                    self.groups_combobox.addItem(group_sorted)
        except Exception:
            show_exception(traceback.format_exc())

    def set_channels_page(self):
        try:
            self.set_channels(
                self.get_channels_page(self.groups_combobox.currentText(), self.page)
            )
        except Exception:
            show_exception(traceback.format_exc())

    def increase_size(self):
        try:
            self.cell_width += self.cell_width_step
            self.create_program_cells()
        except Exception:
            show_exception(traceback.format_exc())

    def decrease_size(self):
        try:
            self.cell_width -= self.cell_width_step
            self.cell_width = max(self.cell_width, self.min_cell_width)
            self.create_program_cells()
        except Exception:
            show_exception(traceback.format_exc())

    def set_day_label(self):
        try:
            self.day_label.setText(self.date.strftime("%A, %d %B %Y"))
            self.check_today()
        except Exception:
            show_exception(traceback.format_exc())

    def check_today(self):
        try:
            if self.cell_current_time is not None:
                if self.date.date() == datetime.datetime.now().date():
                    self.cell_current_time.show()
                    self.cell_current_time.raise_()
                else:
                    self.cell_current_time.hide()
        except Exception:
            show_exception(traceback.format_exc())

    def prev_day(self):
        try:
            self.date -= datetime.timedelta(days=1)
            self.set_day_label()
            self.create_program_cells()
        except Exception:
            show_exception(traceback.format_exc())

    def next_day(self):
        try:
            self.date += datetime.timedelta(days=1)
            self.set_day_label()
            self.create_program_cells()
        except Exception:
            show_exception(traceback.format_exc())

    def move_footer(self):
        try:
            self.footer_widget.move(10, self.height() - self.footer_height)
            self.footer_widget.resize(self.width() - 10, self.footer_height)
        except Exception:
            show_exception(traceback.format_exc())

    def update_scrollarea_size(self):
        try:
            self.scroll_area.setGeometry(
                self.fixed_cell_width,
                50,
                self.width() - self.fixed_cell_width,
                self.height() - 50 - self.footer_height,
            )
        except Exception:
            show_exception(traceback.format_exc())

    def resizeEvent(self, event1):
        try:
            self.update_scrollarea_size()
            self.move_footer()
            super().resizeEvent(event1)
        except Exception:
            show_exception(traceback.format_exc())

    def set_channels(self, channels):
        try:
            self.channels = channels
            self.create_channel_cells()
        except Exception:
            show_exception(traceback.format_exc())

    def format_time(self, time_str):
        try:
            hours, minutes = map(int, time_str.split(":"))
            total_seconds = (hours * 3600) + (minutes * 60)
            return total_seconds
        except Exception:
            show_exception(traceback.format_exc())

    def clear_cells(self):
        try:
            if self.current_cells:
                for cell in reversed(self.current_cells):
                    cell.deleteLater()
                self.current_cells.clear()
        except Exception:
            show_exception(traceback.format_exc())

    def create_channel_cells(self):
        try:
            self.table_widget.setFixedSize(
                self.columns * self.cell_width,
                (len(self.channels) + 1) * self.cell_height,
            )
            self.fixed_column.setGeometry(
                0,
                50,
                self.fixed_cell_width,
                (len(self.channels) + 1) * self.cell_height,
            )
            for channel in range(len(self.channels)):
                channel_label = QtWidgets.QLabel(
                    self.channels[channel], self.fixed_column
                )
                channel_label.setWordWrap(True)
                channel_label.setStyleSheet("border: 1px solid black; padding: 5px;")
                channel_label.move(0, (channel + 1) * self.cell_height)
                channel_label.resize(self.fixed_cell_width, self.cell_height)
                channel_label.show()
        except Exception:
            show_exception(traceback.format_exc())

    def create_hour_cells(self):
        try:
            headers = [f"{str(hour).zfill(2)}:00" for hour in range(24)]
            for col in range(self.columns):
                header_label = QtWidgets.QLabel(headers[col], self.table_widget)
                header_label.setStyleSheet(
                    f"background-color: {self.bg_color}; border: 1px solid black;"
                )
                header_label.move(col * self.cell_width, 0)
                header_label.resize(self.cell_width, self.cell_height)
                header_label.show()
                self.current_cells.append(header_label)
        except Exception:
            show_exception(traceback.format_exc())

    def format_time_cell(self, t):
        try:
            return self.format_time(t.strftime("%H:%M"))
        except Exception:
            show_exception(traceback.format_exc())

    def create_program_cells(self):
        try:
            self.clear_cells()
            self.create_hour_cells()
            day_start = datetime.datetime.combine(self.date.date(), datetime.time())
            day_end = datetime.datetime(
                day_start.year, day_start.month, day_start.day, 23, 59, 59
            )
            for channel in self.channels:
                epg_id = self.get_epg_id(channel)
                if epg_id:
                    epg_programmes = self.get_epg_programmes(epg_id)
                    if epg_programmes:
                        for programme in epg_programmes:
                            if self.epg_is_in_date(programme, day_start):
                                desc = ""
                                if "desc" in programme:
                                    desc = programme["desc"]
                                category = ""
                                if "category" in programme and programme["category"]:
                                    category = f"({programme['category']}) "
                                time_start = datetime.datetime.fromtimestamp(
                                    programme["start"]
                                )
                                time_stop = datetime.datetime.fromtimestamp(
                                    programme["stop"]
                                )
                                _time = (
                                    f"{time_start.strftime('%H:%M')} - "
                                    f"{time_stop.strftime('%H:%M')}"
                                )
                                if time_start < day_start:
                                    time_start = day_start
                                if time_stop > day_end:
                                    time_stop = day_end
                                self.create_cell(
                                    _time,
                                    programme["title"],
                                    desc,
                                    category,
                                    self.format_time_cell(time_start),
                                    self.format_time_cell(time_stop),
                                    channel,
                                )
            self.update_time()
        except Exception:
            show_exception(traceback.format_exc())

    class CellLabel(QtWidgets.QLabel):
        def enterEvent(self, event1):
            try:
                globals()["_multiepg_duration_label"].setText(self._time)
                globals()["_multiepg_name_label"].setText(
                    f"{self._category}{self._text}"
                )
                globals()["_multiepg_desc_label"].setText(self._description)
                self.setStyleSheet("border: 1px solid yellow; padding: 5px;")
                super().enterEvent(event1)
            except Exception:
                show_exception(traceback.format_exc())

        def leaveEvent(self, event1):
            try:
                globals()["_multiepg_duration_label"].setText("")
                globals()["_multiepg_name_label"].setText("")
                globals()["_multiepg_desc_label"].setText("")
                self.setStyleSheet("border: 1px solid black; padding: 5px;")
                super().leaveEvent(event1)
            except Exception:
                show_exception(traceback.format_exc())

    def create_cell(
        self, _time, text, description, category, start_seconds, end_seconds, channel
    ):
        try:
            x_start = int((start_seconds / 3600) * self.cell_width)
            x_end = int((end_seconds / 3600) * self.cell_width)
            channel_row = self.channels.index(channel) + 1

            cell_label = self.CellLabel(text, self.table_widget)
            cell_label.setWordWrap(True)
            cell_label.setStyleSheet("border: 1px solid black; padding: 5px;")
            cell_label._time = _time
            cell_label._text = text
            cell_label._description = description
            cell_label._category = category

            cell_label.move(x_start, channel_row * self.cell_height)
            cell_label.resize(x_end - x_start, self.cell_height)
            cell_label.show()

            self.current_cells.append(cell_label)
        except Exception:
            show_exception(traceback.format_exc())

    def create_current_time_cell(self, start_seconds):
        try:
            x_start = int((start_seconds / 3600) * self.cell_width)

            if self.cell_current_time is not None:
                self.cell_current_time.move(x_start, 0)
            else:
                self.cell_current_time = QtWidgets.QLabel(self.table_widget)
                self.cell_current_time.setStyleSheet("background-color: red;")
                self.cell_current_time.move(x_start, 0)
                self.cell_current_time.resize(1, self.height())
                self.cell_current_time.show()
                self.cell_current_time.raise_()
        except Exception:
            show_exception(traceback.format_exc())

    def update_time(self):
        try:
            self.create_current_time_cell(
                self.format_time(datetime.datetime.now().strftime("%H:%M"))
            )
            self.check_today()
        except Exception:
            show_exception(traceback.format_exc())

    def set_styles(self):
        try:
            self.duration_label.setFont(self.font_italic)
            self.name_label.setFont(self.font_bold)
            self.channel_header_label.setFont(self.font_bold)

            if self.is_dark_theme:
                self.bg_color = "gray"

            self.fixed_column.setStyleSheet(
                f"background-color: {self.bg_color}; border: 1px solid black;"
            )

            self.channel_header_label.setStyleSheet(
                "border: 1px solid black; padding: 5px; "
                f"background-color: {self.bg_color};"
            )
        except Exception:
            show_exception(traceback.format_exc())

    def _set(self, **kwargs):
        try:
            for func in kwargs:
                setattr(self, func, kwargs[func])
            self.set_styles()
        except Exception:
            show_exception(traceback.format_exc())
