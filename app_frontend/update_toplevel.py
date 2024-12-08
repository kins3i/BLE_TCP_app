# -*- coding: utf-8 -*-
""" Class for creating updater GUI and handling update process. """

from __future__ import annotations
from typing import Any, TYPE_CHECKING

import asyncio
import dataclasses
from tkinter import filedialog
import os.path
import threading
import time
import zlib

import customtkinter as ct

try:
    from app_backend.wifi_char import file_characteristic, chunk_characteristic
except ImportError:
    from app_backend.wifi_char_template import (
        file_characteristic,
        chunk_characteristic
    )

from app_frontend.window_shared_utils import set_geometry
from logger_set import logger

if TYPE_CHECKING:
    from app_frontend.gui_main import App

CHUNK_SIZE = 1400


def find_file(title=''):
    """ Get file path from file system. """

    start_path = os.path.join("C:/", "Users")
    path = filedialog.askopenfilename(initialdir=start_path,
                                      filetypes=[('Binary files', '.bin')],
                                      title=title)
    return path


def calc_crc16(crc_input: int, input_arr: bytearray):
    """ Calculate crc16 of given data. """

    crc = crc_input
    data_bytes = input_arr[:]
    data_bytes.append(0)
    data_bytes.append(0)
    for b in data_bytes:
        temp_byte = b | 0x100
        while not temp_byte & 0x10000:
            crc = crc << 1
            temp_byte = temp_byte << 1
            if temp_byte & 0x100:
                crc = crc + 1
            if crc & 0x10000:
                crc = crc ^ 0x1021
        crc = crc & 0xffff

    return crc


@dataclasses.dataclass
class _File:
    crc32_ble: Any = None
    file_arr_ble: Any = None
    file_size_ble: Any = None
    crc32_wifi: Any = None
    file_arr_wifi: Any = None
    file_size_wifi: Any = None


class UpdateWindow(ct.CTkToplevel):
    """ GUI and backend for device updater. """

    def __init__(self, master: App):
        super().__init__()

        w = 800
        h = 600

        set_geometry(self, w, h)

        self.title("Updater")

        self.master = master

        self.child = Updater(self.master, self)

        self.file_type_var = ct.StringVar(value="")
        self.version_var = ct.StringVar(value="0.0.0")

        self.frames = [
            ct.CTkFrame(self),
            ct.CTkFrame(self)
        ]

        self.gui_elements = {
            "file_type_label": ct.CTkLabel(self.frames[0],
                                           text="File type"),
            "file_type_box": ct.CTkComboBox(self.frames[0],
                                            values=["BLE module", "WiFi module", "both"],
                                            variable=self.file_type_var,
                                            state='readonly'),
            "textbox": ct.CTkTextbox(self,
                                     width=600,
                                     corner_radius=0,
                                     wrap='word'),
            "scan_btn": ct.CTkButton(self,
                                     text="Scan and connect",
                                     command=self.scan),
            "version_label": ct.CTkLabel(self.frames[1],
                                         text="Update version"),
            "version": ct.CTkEntry(self.frames[1],
                                   placeholder_text="Update version",
                                   textvariable=self.version_var),
            "submit": ct.CTkButton(self,
                                   text="Send",
                                   command=self.send_file),
            "start_update_btn": ct.CTkButton(self,
                                             text="Start update",
                                             command=self.full_update),
            "go_main_btn": ct.CTkButton(self,
                                        text="Go to main app",
                                        command=self.go_main)
        }


        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self):
        """ Called when window is closed. """

        self.destroy()
        self.master.destroy()

    def go_main(self):
        """ Closes window and go backs to main window. """

        self.destroy()
        self.master.deiconify()
        self.update()

    def run_from_main(self):
        """ Set variables if updater was opened from main window after scan. """

        self.child.run_from_main()

    def scan(self):
        """ Sets GUI for scanning and connecting device. """

        self.child.scan()

    def full_update(self):
        """ Calls main steps of update. """

        self.child.full_update()

    def send_file(self):
        """ Calls function to send file/s to configured device. """

        self.child.send_file()

    def pack_all(self):
        """ Pack all GUI elements. """

        self.frames[0].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.frames[1].pack(expand=True, side="top", fill="x", padx=20, pady=10)
        self.gui_elements["start_update_btn"].pack(expand=True, side="top",
                                                   fill="x", padx=20, pady=10)
        self.gui_elements["file_type_box"].pack(expand=True, side="bottom",
                                                fill="x", padx=20, pady=10)
        self.gui_elements["file_type_label"].pack(expand=True, side="top",
                                                  fill="x", padx=20, pady=10)
        self.gui_elements["version_label"].pack(expand=True, side="top",
                                                fill="x", padx=20, pady=10)
        self.gui_elements["version"].pack(expand=False, side="top", padx=20, pady=10)
        # self.submit.pack(expand=True, side="bottom", fill="x", padx=20, pady=10)
        self.gui_elements["go_main_btn"].pack(expand=True, side="bottom",
                                              fill="x", padx=20, pady=10)


class Updater:
    """ Backend for updater window. """

    def __init__(self, master, window) -> None:
        super().__init__()

        self.master = master

        self.window = window

        self.device = None
        self.client_wifi = None
        self.client_ble = None

        self.file_info = _File()

        self.is_done = False
        self.list_status = None
        self.continue_flag = False
        self.error_flag = False

    def run_from_main(self):
        """ Set variables if updater was opened from main window after scan. """

        if self.master.ble.client_list:
            client = self.master.ble.client_list[0]
            for device_pair in self.master.ble.client_device_list:
                if device_pair[1].client_ble == client:
                    self.device = device_pair[1]
                    self.continue_flag = True
                    self.master.toplevel_window.destroy()
                    self.window.pack_all()
                    self.window.update()
                    self.window.deiconify()
                    self.window.update()
        else:
            logger.error("Error while connecting, no device class was created")
            self.error_flag = False
            self.window.deiconify()
            self.window.update()

    def scan(self):
        """ Sets GUI for scanning and connecting device. """

        self.continue_flag = False
        self.window.withdraw()
        self.master.withdraw()
        self.master.open_toplevel("Please wait! I'm scanning!")
        scan_thread = threading.Thread(target=self._scan_and_connect_thread, args=(), daemon=True)
        scan_thread.start()
        while not self.continue_flag and not self.error_flag:
            continue
        if self.continue_flag:
            self.master.toplevel_window.destroy()
            self.window.pack_all()
            self.window.update()
        else:
            logger.error("Error while connecting, no device class was created")
            self.error_flag = False
        self.window.deiconify()
        self.window.update()

    def _scan_and_connect_thread(self):
        """ Handles scanning and connecting first device on list. """
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.master.ble.scan())
        time.sleep(2)
        if self.master.ble.scanned_devices:
            ble_device = self.master.ble.scanned_devices[0]
            address = ble_device.address
            loop = asyncio.new_event_loop()
            device_pair = loop.run_until_complete(self.master.ble.single_connect(address))
            if device_pair:
                self.device = device_pair[1]
                self.continue_flag = True
            else:
                self.error_flag = True

    def full_update(self):
        """ Calls main steps of update. """

        self.is_done = False
        self.file_info.crc32_ble = None
        self.file_info.file_arr_ble = None
        self.file_info.file_size_ble = None
        self.file_info.crc32_wifi = None
        self.file_info.file_arr_wifi = None
        self.file_info.file_size_wifi = None
        if self.device:
            self.client_ble = self.device.client_ble
            self.device.notifies[2].data.clear()
            self.device.iter_upd_status = 0
        else:
            logger.error("Device doesn't exist, exiting")
            return -1
        self.master.open_toplevel("Please wait! I'm updating!")
        self.window.withdraw()
        response = self._start_update()
        if response == 0:
            logger.debug("Correct update process")
            self.is_done = True
            result = self.send_file()
            if result != 0:
                self.window.destroy()
                self.master.destroy()
                return 0
            self._check_update_status()
            self.master.toplevel_window.destroy()
            self.window.deiconify()
            self.window.update()
            return 0
        if response == -2:
            logger.warning("Critical error")
        elif response == -3:
            logger.warning("Notify error")
        elif response == -4:
            logger.warning("Timeout")
        self.window.destroy()
        self.master.destroy()
        return 0

    def _check_update_status(self):
        file_type_str = self.window.file_type_var.get()
        # TODO: add checking response after successfully sent files for BLE
        #  and both files update
        # needs correct handling of BLE reconnect
        if file_type_str == "WiFi module" and self.client_ble is not None:
            response = self._get_status()
            if response:
                if isinstance(response, list):
                    response = response[1]
                # print("Response:", *response)
                if response[0] == 5:
                    while response[0] == 5:
                        time.sleep(5)
                        response = self._get_status()
                        if isinstance(response, list):
                            response = response[1]
                            # print("Loop response:", *response)
                        else:
                            logger.warning("Error response: %s", response)
                            break
                    if isinstance(response, list):
                        # print("Last response: ", *response)
                        if response[0] == 7:
                            logger.debug("Whole update process ended correctly")
                        elif response[0] == 10:
                            logger.warning("Uploading ESP ended with error")
                    else:
                        logger.warning("Error last response: %s", response)
                else:
                    logger.warning("Error: %s", response)
        elif self.client_ble is None:
            logger.error("None client")

    def _start_update(self):
        """ Sets start-up for update process. """

        response = self._send_update_config()
        if response == -3:
            logger.warning("Error >>start_update<<")
            return -1
        if response != -3:
            start_time = time.time()
            while not self.list_status:
                self.list_status = self.device.get_update_status_notify()
                now_time = time.time() - start_time
                if now_time >= 10.0:
                    logger.warning("My 1st timeout")
                    return -1
            response = self.list_status[0]
            logger.debug("Response 1: %s", response)
            if response[0] == 0xFF:
                if response[1] == 0x01 or response[1] == 0x02 or response[1] == 0x03:
                    logger.warning("Initial conditions not met: %s", response)
                else:
                    logger.warning("Wrong error on initial conditions: %s", response)
                return -1
            if response[0] == 0x00:
                self.list_status.pop(0)
                loop = asyncio.new_event_loop()
                resp = loop.run_until_complete(self.master.ble.write_wifi(client=self.client_ble))
                if resp != 0:
                    return -2
            else:
                logger.warning("Different error! Exiting")
                return -1

            start_time = time.time()
            while not self.list_status:
                self.list_status = self.device.get_update_status_notify()
                now_time = time.time() - start_time
                if now_time >= 41.0:
                    logger.warning("My 2nd timeout")
                    return -1
            response = self.list_status[0]
            logger.debug("Response 2: %s", response)
            if response[0] == 0xFF:
                logger.warning("Device timeout: %s", response)
                return -1
            if response[0] == 0x10:
                logger.warning("Critical error: %s", response)
                return -2
            if response[0] == 0x00:
                self.list_status.pop(0)
            else:
                logger.warning("Different error! %s Exiting", response)
                return -1

            start_time = time.time()
            continue_flag = False
            while not self.list_status:
                self.list_status = self.device.get_update_status_notify()
                now_time = time.time() - start_time
                if now_time < 31.0:
                    if self.device.client_wifi is not None:
                        continue_flag = True
                else:
                    logger.warning("My 3rd timeout")
                    if continue_flag:
                        client_wifi_list = self.device.client_wifi
                        if client_wifi_list is not None:
                            self.client_wifi = client_wifi_list[0]
                        return 0
                    return -1
            response = self.list_status[0]
            logger.debug("Response 3: %s", response)
            if response[0] == 0xFF:
                logger.warning("Device timeout: %s", response)
                return -1
            if response[0] == 0x00:
                self.list_status.pop(0)
                while self.device.client_wifi is None:
                    continue
                client_wifi_list = self.device.client_wifi
                if client_wifi_list is not None:
                    self.client_wifi = client_wifi_list[0]
                    return 0
                logger.error("Couldn't find client in devices")
                return -1
            logger.warning("Different error! Exiting")
            return -1

    def _send_update_config(self):
        """ Creates and sends update config. """
        file_type_str = self.window.file_type_var.get()
        # file_type_int = 0x00
        if file_type_str == "BLE module":
            file_type_int = 0x01
        elif file_type_str == "WiFi module":
            file_type_int = 0x02
        elif file_type_str == "both":
            file_type_int = 0x03
        else:
            file_type_int = 0x00
        update_version_str = self.window.version_var.get().split(".")
        update_version_int = []
        for x in update_version_str:
            a = int(x)
            update_version_int.append(a)
        if update_version_int and file_type_int != 0x00:
            loop = asyncio.new_event_loop()
            if self.client_ble:
                response = loop.run_until_complete(self.master.ble.write_config_update(
                    firmware=file_type_int,
                    upd_nr=update_version_int,
                    client=self.client_ble))
            else:
                response = loop.run_until_complete(self.master.ble.write_config_update(
                    firmware=file_type_int,
                    upd_nr=update_version_int))
            if response == -5:
                logger.warning("Error")
                return -3
            logger.debug("Ended")
            return 0
        return 1

    def _get_status(self):
        """ Gets update status from after update (Wi-Fi update only). """

        if self.client_ble is not None:
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(self.master.ble.read_update_success(self.client_ble))
            if response == -5:
                logger.warning("Error")
                return -3
            return response
        return -1
    def _get_file(self, file_type=""):
        """ Gets physical file from path and prepare file contents. """

        path = ""
        if file_type == "BLE module":
            path = find_file(title="Choose BLE module bin")
        elif file_type == "WiFi module":
            path = find_file(title="Choose WiFi module bin")

        if path:
            file_stats = os.stat(path)
            if file_type == "BLE module":
                self.file_info.crc32_ble = 0
                try:
                    # bin_file = open(path, 'rb')
                    with open(path, 'rb') as bin_file:
                        self.file_info.file_size_ble = file_stats.st_size
                        self.file_info.file_arr_ble = bytearray(bin_file.read())
                        self.file_info.crc32_ble = zlib.crc32(
                            self.file_info.file_arr_ble, self.file_info.crc32_ble)
                        logger.debug("Crc32 BLE: %s Hex: %s",
                                     self.file_info.crc32_ble,
                                     hex(self.file_info.crc32_ble))
                except (ValueError, Exception) as e:
                    logger.error('Error opening or reading binary file')
                    raise Exception(e) from e
            elif file_type == "WiFi module":
                self.file_info.crc32_wifi = 0
                try:
                    with open(path, 'rb') as bin_file:
                        self.file_info.file_size_wifi = file_stats.st_size
                        self.file_info.file_arr_wifi = bytearray(bin_file.read())
                        self.file_info.crc32_wifi = zlib.crc32(
                            self.file_info.file_arr_wifi, self.file_info.crc32_wifi)
                        logger.debug("Crc32 Wi-Fi: %s Hex: %s",
                                     self.file_info.crc32_wifi,
                                     hex(self.file_info.crc32_wifi))
                except (ValueError, Exception) as e:
                    logger.error('Error opening or reading binary file')
                    raise Exception(e) from e
        else:
            return -1

    def _handler_wifi(self, is_ending: bool):
        result = 1
        while result == 1:
            result = self._update_firmware(file_type=0x02,
                                           file_ver=[0, 0, 0],
                                           file_size=self.file_info.file_size_wifi,
                                           crc32=self.file_info.crc32_wifi,
                                           file_arr=self.file_info.file_arr_wifi)
            if result == 0:
                result = self._end_response(is_ending=is_ending)
                if result == 0:
                    logger.debug("Ended update without error")
                elif result == 1:
                    logger.warning("Ended update with crc error")
                else:
                    logger.warning("Client disconnected while ending update")
            elif result == 1:
                break
        return result


    def _handler_ble(self, is_ending: bool):
        result = 1
        while result == 1:
            result = self._update_firmware(file_type=0x01,
                                           file_ver=[0, 0, 0],
                                           file_size=self.file_info.file_size_ble,
                                           crc32=self.file_info.crc32_ble,
                                           file_arr=self.file_info.file_arr_ble)
            if result == 0:
                result = self._end_response(is_ending=is_ending)
                if result == 0:
                    logger.debug("Ended update without error")
                elif result == 1:
                    logger.warning("Ended update with crc error")
                else:
                    logger.warning("Client disconnected while ending in update")
            elif result == 1:
                break
        return result


    def send_file(self):
        """ Calls function to send file/s to configured device. """

        self.is_done = True
        file_type_str = self.window.file_type_var.get()
        if self.is_done:
            if file_type_str == "BLE module":
                res = self._get_file(file_type="BLE module")
                if res != -1:
                    result = self._handler_ble(is_ending=True)
                    logger.debug("Ended update")
                    return result
            elif file_type_str == "WiFi module":
                res = self._get_file(file_type="WiFi module")
                if res != -1:
                    result = self._handler_wifi(is_ending=True)
                    logger.debug("Ended update")
                    return result
            elif file_type_str == "both":
                res = self._get_file(file_type="BLE module")
                if res != -1:
                    res = self._get_file(file_type="WiFi module")
                if res != -1:
                    result = 1
                    error = 0
                    while result == 1:
                        result = self._update_firmware(file_type=0x01,
                                                      file_ver=[0, 0, 0],
                                                      file_size=self.file_info.file_size_ble,
                                                      crc32=self.file_info.crc32_ble,
                                                      file_arr=self.file_info.file_arr_ble)
                        if result == 0:
                            result = self._end_response(is_ending=False)
                            if result == 0:
                                logger.debug("Ended update without error")
                            elif result == 1:
                                logger.warning("Ended update with crc error")
                                error = 1
                                break
                            else:
                                logger.warning("Client disconnected while ending update")
                                error = 1
                        elif result == 1:
                            error = 1
                            break

                    if error == 0:
                        result = self._handler_wifi(is_ending=True)
                    logger.debug("Ended update")
                    return result

    def _update_firmware(self, file_type, file_ver, file_size, crc32, file_arr):
        """ Sets file details for device and calls sending file by chunks. """

        if file_type is None:
            file_type = 0x01

        file_msg = file_characteristic(file_type, file_ver, file_size, crc32)
        # file_str = list(file_msg)
        logger.debug("File char: %s", file_msg)

        response = self.master.wifi.send_with_response(file_msg, self.client_wifi)

        if response:
            if response[0] == 1:
                logger.debug("ok FILE")
                result = 1
                while result == 1:
                    result = self._chunk_send(file_type, file_arr, file_size)
                    if result == -1:
                        logger.warning("Stopped update process due to too many errors")
                        return 1
                    if result == 0:
                        logger.debug("Correct sent chunks")
                        return 0
                logger.warning("Unexpected behavior. result: %s", result)
                return result
            logger.warning("file error: %s", response)
            return 1
        logger.warning("client disconnected")
        return 1

    def _chunk_send(self, file_type, file_arr, file_size):
        """ Sends file chunk by chunk to device. """

        chunk_size = CHUNK_SIZE

        div = divmod(file_size, chunk_size)

        n = div[0] + 1

        iter_frame = 0
        i = 1

        while i < n + 1:
            iter_frame = iter_frame + 1
            if i != n:
                if i == -5:
                    data_chunk = file_arr[(i - 1) * chunk_size: i * chunk_size]
                    crc = 0
                    crc = calc_crc16(crc, data_chunk)
                    chunk_msg = chunk_characteristic(file_type=file_type,
                                                     packet_nr=i,
                                                     packet_size=chunk_size,
                                                     crc16=crc,
                                                     data=data_chunk)
                else:
                    data_chunk = file_arr[(i - 1) * chunk_size: i * chunk_size]
                    crc = 0
                    crc = calc_crc16(crc, data_chunk)
                    chunk_msg = chunk_characteristic(file_type=file_type,
                                                     packet_nr=i,
                                                     packet_size=chunk_size,
                                                     crc16=crc,
                                                     data=data_chunk)
            else:
                data_chunk = file_arr[(i - 1) * chunk_size:]
                crc = 0
                crc = calc_crc16(crc, data_chunk)
                chunk_msg = chunk_characteristic(file_type=file_type,
                                                 packet_nr=i,
                                                 packet_size=div[1],
                                                 crc16=crc,
                                                 data=data_chunk)
            chunk_str = list(chunk_msg)
            len_chunk = len(data_chunk)
            response = self.master.wifi.send_with_response(chunk_msg, self.client_wifi)

            if response[0] == 4:
                logger.debug("ok CHUNK: %s", i)
                i += 1
                iter_frame = 0
            else:
                logger.warning('Chunk: %s len: %s: %s', i, len_chunk, chunk_str[0:12])
                iter_frame += 1
                if response[1] == 0x04:
                    logger.warning("Lost chunk: %s", response)
                elif response[1] == 0x05:
                    logger.warning("Crc16 error: %s", response)
                elif response[1] == 0x10:
                    logger.warning("Data saving error: %s", response)
                elif response[1] == 0x03:
                    logger.warning("Chunk error: %s", response)
                    return -1
                elif response[1] == 0xFF:
                    logger.warning("Critical error, ending update")
                    return -1
        return 0

    def _end_response(self, is_ending=False):
        """ Gets device response after sending all chunks of file. """

        response = self.master.wifi.read_response(timeout=True,
                                                  client=self.client_wifi)
        if response:
            logger.debug("Crc32 response: %s", response)
            if is_ending:
                if response[0] == 0x10:
                    logger.warning("Crc32 error: %s", response)
                    return 1
                if response[0] == 0xFF:
                    logger.debug("Correct CRC32, 0xff (updating) response: %s", response)
                    return 0
                logger.warning("Unknown response: %s", response)
                return 1
            if response[0] == 0x02 or response[0] == 0x03:
                logger.debug("Correct CRC32, next file")
                return 0
            logger.warning("Unknown response: %s", response)
            return 1
        logger.warning("client disconnected")
        return 1
