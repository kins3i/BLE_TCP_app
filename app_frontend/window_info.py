# -*- coding: utf-8 -*-
""" GUI class for presenting full device info. """

from __future__ import annotations
from typing import TYPE_CHECKING

import dataclasses

import customtkinter as ct

from app_frontend.window_shared_utils import (
    set_geometry,
    set_style,
    redirector
)

if TYPE_CHECKING:
    from app_frontend.gui_main import App


@dataclasses.dataclass
class _Info:
    update_nr: list
    firmware_wifi: list
    bootloader: list
    mac_ble: list
    fus: list
    ble_stack: list
    firmware_ble: list
    c_year: int
    c_month: list
    c_day: list
    c_hour: list
    c_minute: list
    mac_wifi: list


class WindowFullInfo(ct.CTkToplevel):
    """ Handles and presents full device info. """

    def __init__(self, master: App):
        super().__init__()
        w = 600
        h = 400

        set_geometry(self, w, h)

        self.title("IMU tester - info")

        self.master = master

        self.label = ct.CTkLabel(self, text="",
                                 justify="center",
                                 font=("Arial", 16, "bold"),
                                 anchor="center", )

        self.textboxes = {
            "upd": ct.CTkTextbox(master=self),
            "ble": ct.CTkTextbox(master=self),
            "wifi": ct.CTkTextbox(master=self),
            "mac_ble": ct.CTkTextbox(master=self),
            "mac_wifi": ct.CTkTextbox(master=self),
            "date": ct.CTkTextbox(master=self),
            "boot": ct.CTkTextbox(master=self),
            "stack": ct.CTkTextbox(master=self),
            "fus": ct.CTkTextbox(master=self),
            "wifi_date": ct.CTkTextbox(master=self)
        }

        color = self.textboxes["upd"].cget('fg_color')

        self.configure(fg_color=color)

        for _, obj in self.textboxes.items():
            set_style(obj=obj, size=12)

        self.label.pack(expand=True, side="top", fill="both")

        for _, obj in self.textboxes.items():
            obj.pack(expand=True, side="top", fill="both")

        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.wm_attributes("-topmost", True)

    def on_exit(self):
        """ Called when window is closed. """

        self.master.deiconify()
        self.master.update()
        self.destroy()


    def show_info(self, response):
        """ Parses data and presents it in readable form. """

        address, data = response
        self.label.configure(text=address)
        list_data = list(data)
        # print("List data: ", *list_data)

        info = _Info(
            update_nr=list_data[0:3],
            firmware_wifi = list_data[3:6],
            bootloader = list_data[6:9],
            mac_ble = list_data[9:15],
            fus = list_data[15:18],
            ble_stack = list_data[18:21],
            firmware_ble = list_data[21:24],
            c_year = int.from_bytes(list_data[24:26], 'little', signed=False),
            c_month = list_data[26],
            c_day = list_data[27],
            c_hour = list_data[28],
            c_minute = list_data[29],
            mac_wifi = list_data[30:36],
        )


        inp_str = (f"Update number: {info.update_nr[0]}."
                   f"{info.update_nr[1]}.{info.update_nr[2]}")
        redirector(self.textboxes["upd"], inp_str)

        inp_str = (f"Wi-Fi firmware: {info.firmware_wifi[0]}."
                   f"{info.firmware_wifi[1]}.{info.firmware_wifi[2]}")
        redirector(self.textboxes["wifi"], inp_str)

        inp_str = (f"BLE firmware: {info.firmware_ble[0]}."
                   f"{info.firmware_ble[1]}.{info.firmware_ble[2]}")
        redirector(self.textboxes["ble"], inp_str)

        inp_str = (f"MAC Wi-Fi: {info.mac_wifi[0]:0>2X}:"
                   f"{info.mac_wifi[1]:0>2X}:"
                   f"{info.mac_wifi[2]:0>2X}:"
                   f"{info.mac_wifi[3]:0>2X}:"
                   f"{info.mac_wifi[4]:0>2X}:"
                   f"{info.mac_wifi[5]:0>2X}")
        redirector(self.textboxes["mac_wifi"], inp_str)

        inp_str = (f"MAC BLE: {info.mac_ble[0]:0>2X}:"
                   f"{info.mac_ble[1]:0>2X}:"
                   f"{info.mac_ble[2]:0>2X}:"
                   f"{info.mac_ble[3]:0>2X}:"
                   f"{info.mac_ble[4]:0>2X}:"
                   f"{info.mac_ble[5]:0>2X}")
        redirector(self.textboxes["mac_ble"], inp_str)

        inp_str = (f"Compilation date: {info.c_hour:02d}:{info.c_minute:02d} "
                   f"{info.c_day:02d}.{info.c_month:02d}.{info.c_year}")
        redirector(self.textboxes["date"], inp_str)

        inp_str = (f"Bootloader version: {info.bootloader[0]}."
                   f"{info.bootloader[1]}.{info.bootloader[2]}")
        redirector(self.textboxes["boot"], inp_str)

        inp_str = (f"BLE stack version: {info.ble_stack[0]}."
                   f"{info.ble_stack[1]}.{info.ble_stack[2]}")
        redirector(self.textboxes["stack"], inp_str)

        inp_str = (f"FUS version: {info.fus[0]}."
                   f"{info.fus[1]}.{info.fus[2]}")
        redirector(self.textboxes["fus"], inp_str)

        if len(list_data) > 40:
            wifi_year = int.from_bytes(list_data[40:42], 'little', signed=False)
            wifi_month = list_data[42]
            wifi_day = list_data[43]
            wifi_hour = list_data[44]
            wifi_minute = list_data[45]

            self.textboxes["wifi_date"].pack(expand=True, side="top", fill="both")

            inp_str = (f"Wi-Fi compilation date: "
                       f"{wifi_hour:02d}:{wifi_minute:02d} "
                       f"{wifi_day:02d}.{wifi_month:02d}.{wifi_year}")
            redirector(self.textboxes["wifi_date"], inp_str)
