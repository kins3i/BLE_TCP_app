# -*- coding: utf-8 -*-
""" GUI class for presenting device ID data. """

from __future__ import annotations
from typing import TYPE_CHECKING

import customtkinter
from bleak import BleakClient
from app_frontend.window_shared_utils import (
    set_geometry,
    set_style,
    redirector
)


if TYPE_CHECKING:
    from app_backend.gui_backend import AppFnc


class WindowDeviceID(customtkinter.CTkToplevel):
    """ Handles and shows serial ID and name of device. """
    def __init__(self, master: AppFnc, client: BleakClient):
        super().__init__()

        w = 600
        h = 400

        set_geometry(self, w, h)

        self.title("Device - ID")

        self.master_back = master
        self.master_ctk = master.master

        self.address = client.address
        self.client = client

        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.wm_attributes("-topmost", True)

        self.frames = [
            customtkinter.CTkFrame(self),
            customtkinter.CTkFrame(self)
        ]

        self.textboxes = {
            "serial": customtkinter.CTkTextbox(master=self.frames[0]),
            "mac_ble": customtkinter.CTkTextbox(master=self.frames[0]),
            "mac_wifi": customtkinter.CTkTextbox(master=self.frames[0])
        }

        self.gui_elem = {
            "label_address": customtkinter.CTkLabel(self.frames[0],
                                                    text="",
                                                    justify="center",
                                                    font=("Arial", 16, "bold"),
                                                    anchor="center", ),
            "label_device_name": customtkinter.CTkLabel(self.frames[0],
                                                        text="",
                                                        font=("Arial", 16, "normal")),
            "name_entry_var": customtkinter.StringVar(value="Device"),
            "name_entry_label": customtkinter.CTkLabel(self.frames[1],
                                                       text="Change device name"),
            "name_entry": customtkinter.CTkEntry(self.frames[1],
                                                 placeholder_text="Name of device",
                                                 textvariable=customtkinter.StringVar()),
            "name_btn": customtkinter.CTkButton(self,
                                                text="Change name",
                                                command=self._write_device_name)

        }

        self.gui_elem["name_entry"].configure(textvariable=self.gui_elem["name_entry_var"])

        set_style(obj=self.textboxes["serial"], size=16)
        set_style(obj=self.textboxes["mac_ble"], size=16)
        set_style(obj=self.textboxes["mac_wifi"], size=16)

        self.create_window()

    def on_exit(self):
        """ Called when window is closed. """

        self.master_ctk.deiconify()
        self.master_ctk.update()
        self.destroy()


    def create_window(self):
        """ Calls function for showing all data. """

        self.frames[0].pack(expand=True, side="top", fill="both")
        self.frames[1].pack(expand=True, side="top", fill="both")

        self.gui_elem["label_address"].pack(expand=True, side="top", fill="both")
        self.textboxes["serial"].pack(expand=True, side="top", fill="both")
        self.textboxes["mac_ble"].pack(expand=True, side="top", fill="both")
        self.textboxes["mac_wifi"].pack(expand=True, side="top", fill="both")
        self.gui_elem["label_device_name"].pack(expand=True, side="top", fill="both")
        self.gui_elem["name_entry_label"].pack(expand=True, side="top", fill="both")
        self.gui_elem["name_entry"].pack(expand=True, side="top", fill="both")
        self.gui_elem["name_btn"].pack(expand=True, side="top", fill="both")

        self._show_serial_id()
        self._read_device_name()

    def _show_serial_id(self):
        """ Gets serial ID and MAC addresses and presents them in textbox. """

        response = self.master_back.get_id(client=self.client)
        if response:
            _, data = response
            self.gui_elem["label_address"].configure(text=self.address)
            list_data = list(data)
            serial_first = chr(list_data[0])
            serial_second = chr(list_data[1])
            serial_number = int.from_bytes(list_data[2:4], 'little', signed=False)
            year = int.from_bytes(list_data[4:6], 'little', signed=False)
            mac_ble = list_data[6:12]
            mac_wifi = list_data[12:18]

            serial_string = serial_first + serial_second + str(serial_number) + "/" + str(year)

            inp_str = (f"MAC Wi-Fi: {mac_wifi[0]:0>2X}:"
                       f"{mac_wifi[1]:0>2X}:"
                       f"{mac_wifi[2]:0>2X}:"
                       f"{mac_wifi[3]:0>2X}:"
                       f"{mac_wifi[4]:0>2X}:"
                       f"{mac_wifi[5]:0>2X}")
            redirector(self.textboxes["mac_wifi"], inp_str)

            inp_str = (f"MAC BLE: {mac_ble[0]:0>2X}:"
                       f"{mac_ble[1]:0>2X}:"
                       f"{mac_ble[2]:0>2X}:"
                       f"{mac_ble[3]:0>2X}:"
                       f"{mac_ble[4]:0>2X}:"
                       f"{mac_ble[5]:0>2X}")
            redirector(self.textboxes["mac_ble"], inp_str)

            inp_str = f"Serial ID: {serial_string:s}"
            redirector(self.textboxes["serial"], inp_str)

    def _set_device_name(self, response):
        """ Sets parsed data in textbox. """

        _, data = response
        data_list = list(data)

        name_list = []
        for x in data_list:
            if x != 0x00:
                name_list.append(x)
            else:
                break

        name_str = [chr(y) for y in name_list]
        name_str = "".join(name_str)
        # print(name_str)

        inp_str = f"Device name: {name_str}"

        self.gui_elem["label_device_name"].configure(text=inp_str)

    def _read_device_name(self):
        """ Gets device name and presents it in textbox. """

        response = self.master_back.get_name(client=self.client)
        if response:
            self._set_device_name(response)

    def _write_device_name(self):
        """ Sets and gets device name and presents it in textbox. """

        name = self.gui_elem["name_entry_var"].get()
        if name:
            response = self.master_back.set_name(client=self.client, name=name)
            if response:
                self._set_device_name(response)
                return 0
            return 1
        return -1
