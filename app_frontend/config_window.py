# -*- coding: utf-8 -*-
""" GUI window for device settings. """

from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass, InitVar

import customtkinter as ct

from app_frontend.window_shared_utils import set_geometry
from logger_set import logger

if TYPE_CHECKING:
    from app_frontend.gui_frames import DeviceFrame


timestamp_dict = {
    "packet": 0x00,
    "frame": 0x01
}

trans_dict = {
    "BLE": 0x00,
    "WiFi": 0x01
}

sleep_mode_dict = {
    "No power saving" : 0x00,
    "Turn off, at all times" : 0x01,
    "Turn off, only in advertising": 0x02,
    "Sleep with WOM": 0x03
}


def reverse_lookup(d, value):
    """ Get dictionary key knowing value only. """

    for key, val in d.items():
        if val == value:
            return key
    return next(iter(d))


@dataclass
class _Labels(ct.CTkLabel):
    master: InitVar[ct.CTkFrame]
    text: InitVar[str]

    def __post_init__(self, master, text):
        super().__init__(master=master, text=text)


class ConfigWindow(ct.CTkToplevel):
    """ Creating GUI and sending device config. """

    def __init__(self, master: DeviceFrame, read_config = None) -> None:
        super().__init__()

        w = 700
        h = 800

        set_geometry(self, w, h)

        self.title("IMU config")

        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.wm_attributes("-topmost", True)

        self.master_window = master.master

        self.frames = [
            ct.CTkFrame(self),
            ct.CTkFrame(self),
            ct.CTkFrame(self),
            ct.CTkFrame(self)
        ]

        self.labels = [
            _Labels(master=self.frames[0], text="Number of packets"),
            _Labels(master=self.frames[1], text="Timestamp with: \n "
                                                "packet \n frame"),
            _Labels(master=self.frames[2], text="Transmission type"),
            _Labels(master=self.frames[3], text="Power saving modes"),
            _Labels(master=self.frames[3], text="Power saving time for BLE"),
            _Labels(master=self.frames[3], text="Power saving time for Wi-Fi")
        ]

        self.vars = [
            ct.StringVar(), # nr of packets
            ct.StringVar(), # timestamp
            ct.StringVar(), # transmission
            ct.StringVar(), # power saving mode
            ct.StringVar(), # st time
            ct.StringVar() # esp time
        ]

        self.entries = {
            "nr_of_packets": ct.CTkComboBox(self.frames[0],
                                            values=["5", "10", "15", "20", "30", "35"],
                                            variable=self.vars[0],
                                            state='readonly'),
            "timestamp": ct.CTkComboBox(self.frames[1],
                                        values=list(timestamp_dict.keys()),
                                        variable=self.vars[1],
                                        state='readonly'),
            "trans_type": ct.CTkComboBox(self.frames[2],
                                         values=list(trans_dict.keys()),
                                         variable=self.vars[2],
                                         state='readonly'),
            "sleep_mode": ct.CTkComboBox(self.frames[3],
                                         values=list(sleep_mode_dict.keys()),
                                         variable=self.vars[3],
                                         state='readonly'),
            "sleep_ble_time": ct.CTkEntry(self.frames[3],
                                          placeholder_text="BLE time",
                                          textvariable=self.vars[4]),
            "sleep_wifi_time": ct.CTkEntry(self.frames[3],
                                           placeholder_text="Wi-Fi time",
                                           textvariable=self.vars[5])
        }

        self.btn_send_config = ct.CTkButton(self, text="Send config",
                                        command=self.send_config)

        self.pack_all()

        if read_config:
            # print(read_config)
            self.set_read_values(read_config[1])
            self.deiconify()
            self.update()
        else:
            self.set_default_values()

    def on_exit(self):
        """ Called when closing window. """

        self.master_window.deiconify()
        self.master_window.update()
        self.destroy()

    def set_default_values(self):
        """ Setting default entries and boxes values. """

        self.vars[0].set("10")
        self.vars[1].set("packet")
        self.vars[2].set("BLE")
        self.vars[3].set("No power saving")
        self.vars[4].set("0")
        self.vars[5].set("0")

    def set_read_values(self, data):
        """ Setting entries and boxes values from device config. """

        nr_of_packets = str(data[3])
        self.vars[0].set(nr_of_packets)

        timestamp = data[2]
        timestamp_key = reverse_lookup(timestamp_dict, timestamp)
        self.vars[1].set(timestamp_key)

        trans_type = data[5]
        trans_key = reverse_lookup(trans_dict, trans_type)
        self.vars[2].set(trans_key)

        if len(data) > 8:
            sleep_mode = data[7]
            sleep_mode_key = reverse_lookup(sleep_mode_dict, sleep_mode)
            self.vars[3].set(sleep_mode_key)

            sleep_time1_var = str(data[8])
            self.vars[4].set(sleep_time1_var)

            sleep_time2_var = str(data[9])
            self.vars[5].set(sleep_time2_var)

    def pack_all(self):
        """ Pack all GUI elements. """

        for f in self.frames:
            f.pack(expand=True, side="top", fill="x", padx=10, pady=10)

        self.labels[0].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.entries['nr_of_packets'].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.labels[1].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.entries['timestamp'].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.labels[2].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.entries['trans_type'].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.labels[3].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.entries['sleep_mode'].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.labels[4].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.entries['sleep_ble_time'].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.labels[5].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.entries['sleep_wifi_time'].pack(expand=True, side="top", fill="x", padx=20, pady=10)

        self.btn_send_config.pack(expand=True, side="top", fill="x", padx=20, pady=10)

    def send_config(self):
        """ Get arguments and call config setting function. """

        nr_of_meas = int(self.entries['nr_of_packets'].get())

        time_ble = 0
        time_wifi = 0

        if self.entries['sleep_ble_time'].get():
            try:
                time_ble = int(self.entries['sleep_ble_time'].get())
                time_ble = min(time_ble, 255)
            except ValueError as e:
                logger.warning("ST time not int: %s", e)
                time_str = ''.join(filter(str.isdigit, self.entries['sleep_ble_time'].get()))
                if time_str:
                    time_ble = int(time_str)
                else:
                    time_ble = 0
            except Exception as e:
                logger.error("BLE exception: %s", e)

        if self.entries['sleep_wifi_time'].get():
            try:
                time_wifi = int(self.entries['sleep_wifi_time'].get())
                time_wifi = min(time_wifi, 255)
            except ValueError as e:
                logger.error("ESP time not int: %s", e)
                time_str = ''.join(filter(str.isdigit, self.entries['sleep_wifi_time'].get()))
                if time_str:
                    time_wifi = int(time_str)
                else:
                    time_wifi = 0
            except Exception as e:
                logger.error("ESP exception: %s", e)

        timestamp = timestamp_dict.get(self.entries['timestamp'].get(), 0)
        transmission = trans_dict.get(self.entries['trans_type'].get(), 0)
        power_mode = sleep_mode_dict.get(self.entries['sleep_mode'].get(), 0)

        self.master_window.set_config(nr_of_meas=nr_of_meas,
                                      timestamp=timestamp,
                                      transmission=transmission,
                                      power_mode=power_mode,
                                      time_ble=time_ble,
                                      time_wifi=time_wifi)

        # print(nr_of_meas, timestamp, transmission, power_mode, time_ble, time_wifi)
