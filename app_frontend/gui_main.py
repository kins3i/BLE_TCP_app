# -*- coding: utf-8 -*-
""" Main class for creating and handling GUI. """

import asyncio
import sys
import tkinter

from bleak.backends.winrt.util import allow_sta
import customtkinter

from app_backend.gui_backend import AppFnc
from app_frontend.gui_frames import DeviceFrame
from app_frontend.toplevel_waiting import ToplevelWindow
from app_frontend.update_toplevel import UpdateWindow
from app_frontend.window_shared_utils import set_geometry

from logger_set import logger

sys.coinit_flags = 0  # 0 means MTA


class App(customtkinter.CTk):
    """ Class for handling all GUI frontend. """

    def __init__(self):
        super().__init__()

        w = 1200
        h = 800

        set_geometry(self, w, h)

        self.title("App")

        self.toplevel_window = None

        self.back_app = AppFnc(self)

        self.ble = self.back_app.ble
        self.wifi = self.back_app.wifi

        self.window_upd = None

        # add widgets to app
        self.buttons_frame = customtkinter.CTkFrame(self)
        self.buttons_frame.configure(fg_color='transparent')
        self.buttons_frame.pack(expand=True, side="top", fill="both", padx=20, pady=10)

        self.textbox = customtkinter.CTkTextbox(master=self, width=400, height=100,
                                                corner_radius=0, wrap='word')

        self.device_frame = DeviceFrame(master=self)
        self.device_frame.create_device_frames(self)

        self.scan_btn = customtkinter.CTkButton(master=self.buttons_frame,
                                                text="Scan", command=self._btn_scan)
        self.scan_btn.pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.update_btn = customtkinter.CTkButton(self.buttons_frame, text="Do update",
                                                  command=self._open_update_window)
        self.update_btn.pack(expand=True, side="top", fill="x", padx=20, pady=10)

        try:
            allow_sta()
        except ImportError:
            pass

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    # add methods to app
    def on_exit(self):
        """ Called when window is closed. """

        self.back_app.on_close()
        self.destroy()
        sys.exit(0)

    def _btn_scan(self):
        """ Set all GUI elements on scan. """

        self.textbox.delete('0.0', "end")
        self.device_frame.unpack_bts()
        self.device_frame.create_device_frames(self)

        self.withdraw()
        self.open_toplevel("Please wait! I'm scanning!")

        self.back_app.scan()

        self.deiconify()
        self.toplevel_window.destroy()

        if self.ble.scanned_devices:
            self._print_device()
            self._device_frame_pack()
            self.device_frame.pack_connection_bts()
            self.device_frame.create_boxes()

        if self.ble.client_list:
            self.device_frame.pack_conf_box()

        self.update()

    def one_connect(self, address):
        """ Calls backend for device connect. """

        self.device_frame.pack_conf_box()
        client = self.back_app.one_connect(address)
        return client

    def one_disconnect(self, address):
        """ Calls backend for device disconnect. """

        self.back_app.one_disconnect(address)

    def get_config(self):
        """ Calls backend for getting device config. """

        response = self.back_app.get_conf()
        return response

    def set_config(self, **kwargs):
        """ Calls backend for setting device config. """

        response = self.back_app.set_conf(**kwargs)
        self.textbox.delete('0.0', "end")
        for element in response:
            address, data = element
            self.redirector(str(address) + ", (config): ")
            self.redirector(str(data) + "\n")
        response = self.back_app.get_battery()
        for element in response:
            address, data = element
            list_data = list(data)
            self.redirector(str(address) + ", (battery): ")
            self.redirector(str(list_data) + "\n")

    def get_device_info(self):
        """ Calls backend for setting full device info. """

        self.back_app.get_device_info()

    def get_wifi(self):
        """ Calls backend for getting Wi-Fi config. """

        response = self.back_app.get_wifi()
        self.textbox.delete('0.0', "end")
        for element in response:
            address, data = element
            ssid = ''.join([chr(i) for i in data[0:32]])
            ssid = ssid.replace('\x00', '0')
            psw = ''.join([chr(i) for i in data[32:64]])
            psw = psw.replace('\x00', '0')

            decoded_response = [ssid, psw]
            for i in range(64, 80):
                decoded_response.append(data[i])

            self.redirector(str(address) + ", (wifi):\n")
            self.redirector(str(decoded_response) + "\n")
            self.redirector(str(data) + "\n")

    def set_wifi(self):
        """ Calls backend for setting Wi-Fi config. """

        self.back_app.set_wifi()
        self.get_wifi()

    def get_device_ids(self):
        """ Calls backend for getting device's serial info. """

        self.back_app.get_device_ids()

    def cmd_conn_wifi(self):
        """ Calls backend for sending Wi-Fi connect action. """

        self.device_frame.box_start_stop.configure(state=tkinter.DISABLED)
        self.back_app.set_action("connect_wifi")
        self.device_frame.box_start_stop.configure(state=tkinter.NORMAL)

    def synchronize(self):
        """ Calls backend for sending Wi-Fi connect action. """

        self.back_app.set_action("synchronize")

    def identify(self):
        """ Calls backend for sending identify action. """

        self.back_app.set_action("identify")

    def turn_off(self):
        """ Calls backend for sending turning off action. """

        self.back_app.set_action("turn_off")

    def reset(self):
        """ Calls backend for sending reset action. """

        self.back_app.set_action("reset")

    def start_data(self):
        """ Calls backend for sending start data action. """

        self.back_app.start_data()

    def stop_data(self):
        """ Calls backend for sending stop data action. """

        self.back_app.stop_data()

    def redirector(self, input_str):
        """ Sets text in textbox. """

        self.textbox.insert('end', input_str)

    def _print_device(self):
        """ Sets all scanned devices in textbox. """

        if self.ble.scanned_devices:
            self.textbox.pack(after=self.buttons_frame, side="top", fill="both",
                              padx=20, pady=10)
            for dev in self.ble.scanned_devices:
                self.redirector(str(dev.name) + " " + str(dev.address) + "\n")
        else:
            logger.debug("Empty device list")

    def _device_frame_pack(self):
        """ Pack GUI part. """

        self.device_frame.pack(after=self.textbox, expand=True, side="top",
                               fill="x", padx=20, pady=10)
        self.device_frame.configure(fg_color='transparent')

    def open_toplevel(self, string):
        """ Sets waiter window. """

        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow()
            # create window if its None or destroyed
            self.toplevel_window.label.configure(text=string)
            self.toplevel_window.update()
            self.toplevel_window.deiconify()
            self.toplevel_window.update()
        else:
            self.toplevel_window.focus()  # if window exists focus it

    def _open_update_window(self):
        """ Opens updater window and hides main window. """

        if self.window_upd is None or not self.window_upd.winfo_exists():
            self.window_upd = UpdateWindow(master=self)
            self.withdraw()
            if self.ble.client_list:
                self.window_upd.run_from_main()
            else:
                self.window_upd.gui_elements["scan_btn"].pack(expand=True,
                                                              side="top",
                                                              fill="x",
                                                              padx=20,
                                                              pady=10)
