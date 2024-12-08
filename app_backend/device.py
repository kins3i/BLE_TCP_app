# -*- coding: utf-8 -*-
""" Module for joining Bleak and TCP client. """

import asyncio
import dataclasses
import threading
from typing import (Callable, Union, Awaitable)
import uuid

from bleak import BleakGATTCharacteristic

from logger_set import logger
try:
    from .ble_char import Characteristics
except ImportError:
    from .ble_char_template import Characteristics
from .parser import meas_data_parser


@dataclasses.dataclass
class _Notify:
    flag: bool
    order: uuid.UUID
    callback: Callable[
        [BleakGATTCharacteristic, bytearray], Union[None, Awaitable[None]]
    ]
    id: str
    data: list
    _data: list = dataclasses.field(init=False, repr=False)


    @property
    def data(self) -> list:
        """ Notify content."""

        return self._data

    @data.setter
    def data(self, value) -> None:
        self._data = value


class Device:
    """ Class for connecting BLE and Wi-Fi client and managing notifies.

    Allows connecting BLE client with Wi-Fi client, manages notifies and parses
    measurement data.

    Attributes:
        client_ble: BleakClient
        address_ble: list[int]
        address_wifi: list[int]
        mac_ble: str
        mac_wifi: str
        client_wifi
        chars: Characteristics
        notifies: list[_Notify]
        iter_upd_status: int
        _stop_flag: bool
        configure: None, list

    """

    def __init__(self, client_ble, address_ble, address_wifi):
        self.client_ble = client_ble
        self.address_ble = address_ble
        self.address_wifi = address_wifi
        self.mac_ble = (f"{self.address_ble[0]:0>2X}:"
                       f"{self.address_ble[1]:0>2X}:"
                       f"{self.address_ble[2]:0>2X}:"
                       f"{self.address_ble[3]:0>2X}:"
                       f"{self.address_ble[4]:0>2X}:"
                       f"{self.address_ble[5]:0>2X}")
        self.mac_wifi = (f"{self.address_wifi[0]:0>2X}:"
                        f"{self.address_wifi[1]:0>2X}:"
                        f"{self.address_wifi[2]:0>2X}:"
                        f"{self.address_wifi[3]:0>2X}:"
                        f"{self.address_wifi[4]:0>2X}:"
                        f"{self.address_wifi[5]:0>2X}")
        self.client_wifi = None

        self.chars = Characteristics()

        self.notifies = [
            _Notify(flag=True,
                    data=[],
                    order=self.chars.ble_get_status()[0],
                    callback=self._dev_status_callback,
                    id="dev status"),
            _Notify(flag=True,
                    data=[],
                    order=self.chars.ble_data()[0],
                    callback=self._data_callback,
                    id="data"),
            _Notify(flag=True,
                    data=[],
                    order=self.chars.ble_update_status()[0],
                    callback=self._update_status_callback,
                    id="update status")
        ]

        self.iter_upd_status = 0
        self._stop_flag = False
        self.configure = None

        logger.debug("BLE MAC: %s, Wi-Fi MAC: %s", self.mac_ble, self.mac_wifi)

        self.start_notifies()

    def get_update_status_notify(self):
        """ Returns update status list. """

        return self.notifies[2].data

    def start_notifies(self):
        """ Starts all notify readings.

        Starts and awaits on all notifies from devices.
        Every notify is awaited in different thread.
        """

        listening_thread = threading.Thread(target=self.async_device_status,
                                            args=(), daemon=True)
        listening_thread.start()
        listening_thread = threading.Thread(target=self.async_data,
                                            args=(), daemon=True)
        listening_thread.start()
        listening_thread = threading.Thread(target=self.async_update_status,
                                            args=(), daemon=True)
        listening_thread.start()

    def _dev_status_callback(self, sender: BleakGATTCharacteristic, data: bytearray):  # N
        """ Called each time device status appears.

        Prints data received via device status notify.
        """

        _ = sender

        list_data = list(data)
        if list_data[0] == 0x05:
            time_b = list_data[1:5]
            time_int = int.from_bytes(time_b, 'little', signed=False)
            logger.debug("Data: %s, time: %s", list_data, time_int)
        else:
            logger.debug("Data: %s", list_data)
        self.notifies[0].data.append(list_data)

    def _data_callback(self, sender: BleakGATTCharacteristic, data: bytearray):  # N
        """ Called each time data appears.

        Gets and parses data received via data notify.
        Data returned form parser is set into list.
        """

        _ = sender
        if self.configure:
            resp = meas_data_parser(data, self.configure, self.mac_ble)
            self.notifies[1].data = []
            if resp:
                date, mac, print_str = resp
                self.notifies[1].data.append(date)
                self.notifies[1].data.append(mac)
                self.notifies[1].data.append(print_str)

    def _update_status_callback(self, sender: BleakGATTCharacteristic, data: bytearray):  # N
        """ Called each time update status appears.

        Prints data received via update status notify.
        """

        _ = sender

        self.iter_upd_status += 1
        logger.debug("Status Data: %s, iteration: %s ", data, self.iter_upd_status)
        self.notifies[2].data = [data]
        # self.n_5005_data.append(data)

    def _handler_disconnected_device(self):
        self.stop_all_notifies()

    async def _handle_notifies(self, notif_class: _Notify):
        """ Starts update status notify.

        Returns:
            0, if notify stopped correctly; -5 if value error or exception is caught.

        Raises:
            ValueError, Exception: error occurred when awaiting notify GATT service.
        """

        # flag = notif_class.flag
        # order = notif_class.order
        # callback = notif_class.callback

        notif_class.flag = True
        if self.client_ble.is_connected and notif_class.order is not None:
            try:
                await self.client_ble.start_notify(notif_class.order, notif_class.callback)
                logger.debug("Started notify %s", notif_class.id)
                while True:
                    await asyncio.sleep(0.5)
                    if not notif_class.flag:
                        if self.client_ble.is_connected:
                            await self.client_ble.stop_notify(notif_class.order)
                        else:
                            logger.warning("Client disconnected too early")
                        break
                    if not self.client_ble.is_connected:
                        self._handler_disconnected_device()
                        break
                self._stop_flag = True
                logger.debug("Stopped notify %s", notif_class.id)
                return 0
            except (ValueError, Exception) as e:
                logger.error('Error in notify %s: %s', notif_class.id, e)
                self._handler_disconnected_device()
                return -5
        else:
            logger.warning("Client: %s not connected", self.address_ble)

    def async_device_status(self):
        """ Starts asyncio loop for device status notify. """

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._handle_notifies(self.notifies[0]))

    def async_data(self):
        """ Starts asyncio loop for data notify. """

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._handle_notifies(self.notifies[1]))

    def async_update_status(self):
        """ Starts asyncio loop for update status notify. """

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._handle_notifies(self.notifies[2]))

    def stop_all_notifies(self):
        """ Sets flags for gracefully stopping all notifies.

        Returns:
            1
        """

        self._stop_flag = False
        for notif in self.notifies:
            self._stop_flag = False
            notif.flag = False
            while not self._stop_flag:
                continue
        return 1
