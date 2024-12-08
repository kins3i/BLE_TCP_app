# -*- coding: utf-8 -*-
""" Class for creating GUI objects. """

from __future__ import annotations
from typing import TYPE_CHECKING

import tkinter
import threading

import customtkinter as ct

from app_frontend.config_window import ConfigWindow

if TYPE_CHECKING:
    from app_frontend.gui_main import App


class DeviceFrame(ct.CTkFrame):
    """ Create and handle elements of GUI. """

    def __init__(self, master: App):
        super().__init__(master)

        self.master = master
        self.ble = master.ble

        self.check_frame = None
        self.params_frame = None
        self.start_frame = None
        self.buttons_frame = None

        self.btn_connect_all = None
        self.btn_disconnect_all = None

        self.box_start_stop = None
        self.start_stop_var = tkinter.IntVar(value=0)
        self.btn_wifi_connect = None
        self.btn_identify = None
        self.btn_synchro = None
        self.btn_turn_off = None
        self.btn_reset = None
        self.btn_send_config = None
        self.btn_device_info = None
        self.btn_get_wifi = None
        self.btn_set_wifi = None
        self.btn_device_id = None

        self.check_buttons = []

    def create_device_frames(self, master):
        """ Set all GUI elements beside devices checkboxes. """

        self.check_frame = ct.CTkFrame(self)
        self.params_frame = ct.CTkFrame(self)
        self.buttons_frame = ct.CTkFrame(self.params_frame)
        self.start_frame = ct.CTkFrame(self.params_frame)

        self.btn_connect_all = ct.CTkButton(master.buttons_frame,
                                            text="Connect all",
                                            command=self.btn_connect)
        self.btn_disconnect_all = ct.CTkButton(master.buttons_frame, text="Disconnect all",
                                               command=self.btn_disconnect)

        self.btn_send_config = ct.CTkButton(self.buttons_frame, text="Choose config",
                                            command=self.start_config)

        self.btn_device_info = ct.CTkButton(self.buttons_frame, text="Get device info",
                                            command=self.master.get_device_info)

        self.btn_device_id = ct.CTkButton(self.buttons_frame, text="Get device ID",
                                          command=self.master.get_device_ids)

        self.btn_set_wifi = ct.CTkButton(self.buttons_frame, text="Set WiFi",
                                         command=self.master.set_wifi)
        self.btn_get_wifi = ct.CTkButton(self.buttons_frame, text="Get WiFi",
                                         command=self.master.get_wifi)

        self.btn_wifi_connect = ct.CTkButton(self.start_frame, text="Connect to WiFi",
                                             command=self.master.cmd_conn_wifi)
        self.btn_synchro = ct.CTkButton(self.start_frame, text="Synchronize",
                                        command=self.master.synchronize)
        self.btn_identify = ct.CTkButton(self.start_frame, text="Identify",
                                         command=self.master.identify)
        self.btn_turn_off = ct.CTkButton(self.start_frame, text="Turn off",
                                         command=self.master.turn_off)
        self.btn_reset = ct.CTkButton(self.start_frame, text="Reset",
                                         command=self.master.reset)
        self.box_start_stop = ct.CTkCheckBox(self.start_frame, onvalue=1, offvalue=0,
                                             text="Start/stop data",
                                             variable=self.start_stop_var,
                                             command=self.event_start_stop)

    def checkbox_event(self, btn):
        """ Set function to be called when checkbox state is changed. """

        name_address = btn.cget("text")
        var = btn.cget("variable")
        address = name_address.split()[1]
        if var.get() == 1:
            thr_connect = threading.Thread(target=self.master.one_connect,
                                           args=(address,), daemon=True)
            thr_connect.start()
        elif var.get() == 0:
            thr_disconnect = threading.Thread(target=self.master.one_disconnect,
                                              args=(address,), daemon=True)
            thr_disconnect.start()

    def start_config(self):
        """ Call parent's read config and sets config GUI. """

        response = self.master.get_config()
        if response:
            ConfigWindow(master=self, read_config=response[0])
        else:
            ConfigWindow(master=self)

    def connect_threading(self, button, address):
        """ Calls connecting device and checks checkbox. """

        client = self.master.one_connect(address)
        if client[0] is not None:
            button.select()

    def disconnect_threading(self, button, address):
        """ Calls disconnecting device and unchecks checkbox. """

        self.master.one_disconnect(address)
        button.deselect()

    def btn_connect(self):
        """ Sets connecting thread for every button. """
        self.pack_conf_box()
        for btn in self.check_buttons:
            address = btn.cget("text").split()[1]
            thr_connect = threading.Thread(target=self.connect_threading,
                                           args=([btn, address, ]), daemon=True)
            thr_connect.start()

    # TODO: deselect each button after device is disconnected without blocking each process
    def btn_disconnect(self):
        """ Sets disconnecting thread for every button. """
        for btn in self.check_buttons:
            address = btn.cget("text").split()[1]
            thr_disconnect = threading.Thread(target=self.disconnect_threading,
                                              args=([btn, address, ]), daemon=True)
            thr_disconnect.start()

    def event_start_stop(self):
        """ Sets threading for starting and stopping data on checkbox. """

        if self.start_stop_var.get() == 1:
            thr_connect = threading.Thread(target=self.master.start_data, args=())
            thr_connect.start()
        elif self.start_stop_var.get() == 0:
            thr_disconnect = threading.Thread(target=self.master.stop_data, args=())
            thr_disconnect.start()

    def _check_connected(self, address):
        """ Sets checkbox if address is already connected. """

        for cl in self.ble.client_list:
            if cl.address == address:
                return 1
        return 0

    def create_boxes(self):
        """ Sets and packs all devices checkboxes. """

        if self.ble is not None:
            if self.ble.nr_of_devices > 0:
                self.check_frame.pack(expand=True, side="left", fill="x", padx=20, pady=10)
                for sc_dev in self.ble.scanned_devices:
                    state = self._check_connected(sc_dev.address)
                    string = str(sc_dev.name + " " + sc_dev.address)
                    btn = ct.CTkCheckBox(self.check_frame,
                                         onvalue=1,
                                         offvalue=0,
                                         text=string,
                                         variable=tkinter.IntVar(value=state),
                                         )
                    self.check_buttons.append(btn)
                    btn.configure(command=lambda b=btn: self.checkbox_event(b))
                    btn.pack(expand=True, side="top", fill="x", padx=20, pady=10)

    def pack_conf_box(self):
        """ Pack all GUI elements beside devices checkboxes. """

        self.params_frame.pack(after=self.check_frame, expand=True, side="left",
                               fill="x", padx=20, pady=10)
        self.start_frame.pack(expand=True, side="left", fill="x", padx=20, pady=10)
        self.buttons_frame.pack(expand=True, side="right", fill="x", padx=20, pady=10)

        self.btn_connect_all.pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.btn_disconnect_all.pack(expand=True, side="top", fill="x", padx=20, pady=10)

        self.btn_set_wifi.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.btn_get_wifi.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.btn_synchro.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.btn_identify.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.btn_turn_off.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.btn_reset.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.btn_wifi_connect.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.box_start_stop.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)

        self.btn_device_id.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.btn_device_info.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.btn_send_config.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)

    def pack_connection_bts(self):
        """ Pack connect and disconnect buttons. """

        self.btn_connect_all.pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.btn_disconnect_all.pack(expand=True, side="top", fill="x", padx=20, pady=10)

    def unpack_bts(self):
        """ Destroy all GUI elements. """

        self.btn_connect_all.destroy()
        self.btn_disconnect_all.destroy()
        for x in self.check_buttons:
            x.destroy()
        self.check_frame.destroy()
        self.check_buttons = []

        self.params_frame.destroy()
        self.buttons_frame.destroy()

        self.btn_set_wifi.destroy()
        self.btn_get_wifi.destroy()
        self.btn_wifi_connect.destroy()

        self.btn_send_config.destroy()
