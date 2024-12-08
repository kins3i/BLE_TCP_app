# -*- coding: utf-8 -*-
""" Main GUI class. """

from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
import time
import threading

from bleak import BleakClient

from app_frontend.window_id import WindowDeviceID
from app_frontend.window_info import WindowFullInfo

from logger_set import logger

from .ble_main import Bluetooth
from .wifi_server import WiFi

if TYPE_CHECKING:
    from app_frontend.gui_main import App


class AppFnc:
    """ Class handling backend for GUI.

        Calls every external backend class or function to relieve GUI code.

        Attributes:
            master: App
            ble: Ble
            wifi: WiFi
            wifi_response: threading.Thread
            loop: coroutine
            transmission_type: int

        """

    def __init__(self, master: App):
        self.master = master

        self.ble = Bluetooth()
        self.wifi = WiFi()
        self.ble.wifi_clients = self.wifi.clients
        self.wifi_response = threading.Thread(target=self.wifi.create_server, args=(), daemon=True)
        self.wifi_response.start()

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.transmission_type = None

    def on_close(self):
        """ Function called when closing GUI.

        Gracefully ends all processes on BLE and TCP.
        Prints last BLE measurement (if exists).
        """

        for device in self.ble.client_device_list:
            dev = device[1]
            data_notify = dev.notifies[1].data
            if data_notify:
                local_time = data_notify[0]
                mac = data_notify[1]
                data = data_notify[2]
                logger.debug("Device %s on close: %s %s", mac, local_time, data)
        self.ble.on_close()
        self.wifi.on_close()

    def scan(self):
        """ Runs BLE scanner. """

        self.loop.run_until_complete(self.ble.scan())

    def one_connect(self, address):
        """ Calls connect function on BLE device.

        Returns:
            [BleakClient, Device] or [None, None] when error is caught.
        """

        loop = self.loop
        while loop.is_running():
            time.sleep(0.1)
        asyncio.set_event_loop(loop)
        client = loop.run_until_complete(self.ble.single_connect(address))
        self.wifi.dev_classes = self.ble.client_device_list
        return client

    def one_disconnect(self, address):
        """ Calls disconnect function on BLE device. """

        loop = self.loop
        while loop.is_running():
            time.sleep(0.1)
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.ble.single_disconnect(address))

    def get_conf(self):
        """ Calls reading device config on all BLE devices.

        Returns:
            list of responses like: [address, config]
        """

        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(self.ble.read_config())
        return response

    def set_conf(self, **kwargs):
        """ Calls writing and reading device config on all BLE devices.

        Returns:
            list of responses like: [address, config]
        """

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.ble.write_config(**kwargs))
        response = self.get_conf()
        for element in response:
            _, data = element
            list_data = list(data)
            transmission_type = list_data[5]
            if self.transmission_type != transmission_type:
                self.transmission_type = transmission_type
        return response

    def get_device_info(self):
        """ Calls GUI for handling device full info. """

        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(self.ble.read_dev_info())
        for element in response:
            device_info = WindowFullInfo(self.master)
            device_info.lift()
            device_info.show_info(element)

    def get_wifi(self):
        """ Calls reading Wi-Fi config on all BLE devices.

        Returns:
            list of responses like: [address, Wi-Fi config]
        """

        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(self.ble.read_wifi())

        return response

    def set_wifi(self):
        """ Calls writing Wi-Fi config on all BLE devices. """

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.ble.write_wifi())

    def get_device_ids(self):
        """ Calls GUI for handling device serial info. """

        for client in self.ble.client_list:
            WindowDeviceID(master=self, client=client)

    def get_battery(self):
        """ Calls reading battery info on all BLE devices.

        Returns:
            list of responses like: [address, battery info]
        """

        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(self.ble.read_battery())

        return response

    def get_id(self, client: BleakClient):
        """ Calls reading serial info on BLE client.

        Returns:
            response like: [address, battery info]
        """

        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(self.ble.read_id(client=client))

        return response

    def get_name(self, client: BleakClient):
        """ Calls reading device name on BLE client.

        Returns:
            response like: [address, battery info]
        """

        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(self.ble.read_name(client=client))

        return response

    def set_name(self, client: BleakClient, name: str = ""):
        """ Calls writing and reading device name on BLE client.

        Returns:
            response like: [address, name]
        """

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.ble.write_name(client=client, name=name))

        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(self.ble.read_name(client=client))

        return response

    def set_action(self, action_type: str = ""):
        """ Invokes action based on string argument. """

        loop = asyncio.new_event_loop()
        match action_type:
            case "identify":
                loop.run_until_complete(self.ble.write_action(action=0))
            case "connect_wifi":
                loop.run_until_complete(self.ble.write_action(action=2))
            case "synchronize":
                loop.run_until_complete(self.ble.write_action(action=4))
            case "turn_off":
                loop.run_until_complete(self.ble.write_action(action=5))
            case "reset":
                loop.run_until_complete(self.ble.write_action(action=6))
            case _:
                pass

    def _wifi_listen_clients(self):
        """ Invokes thread for awaiting on TCP server. """

        listening_thread = threading.Thread(target=self.wifi.listen_on_socket(),
                                            args=(), daemon=True)
        listening_thread.start()

    def start_data(self):
        """ Invokes start of data receiving via BLE or TCP. """

        if self.transmission_type is None:
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(self.ble.read_config())
            for element in response:
                _, data = element
                list_data = list(data)
                transmission_type = list_data[5]
                if self.transmission_type != transmission_type:
                    self.transmission_type = transmission_type
        if self.transmission_type == 1:  # WiFi
            self._wifi_listen_clients()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.ble.write_data_action(action=0x01))

    def stop_data(self):
        """ Invokes stop of data receiving. """

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.ble.write_data_action(action=0x00))
