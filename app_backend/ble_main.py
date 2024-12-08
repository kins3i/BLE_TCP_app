# -*- coding: utf-8 -*-
""" Module for handling BLE actions. """

import asyncio
from datetime import datetime

from bleak import BleakClient, BleakCharacteristicNotFoundError
from bleak import BleakScanner

try:
    import credentials as cr
except ImportError:
    import credentials_template as cr

from logger_set import logger

try:
    from .ble_char import Characteristics
except ImportError:
    from .ble_char_template import Characteristics

from .device import Device


class Bluetooth:
    """ Class for managing BLE functionalities.
    Allows scanning, connecting, disconnecting and using all BLE characteristics.

    Attributes:
        scanned_devices : list
            all BleakScanner instances
        client_list : list
            all BleakClient class instances
        client_device_list : list
            all Device class instances
        nr_of_devices: int
            number of devices in scanned_devices
        wifi_clients: None, list
            if not None, list contains all devices connected via Wi-Fi to server

     """

    def __init__(self):
        self.scanned_devices = []
        self.client_list = []
        self.client_device_list = []
        self.nr_of_devices = 0
        self.wifi_clients = None
        self.chars = Characteristics()

    def on_close(self):
        """ Gracefully stops all BleakClients notifies."""

        for device in self.client_device_list:
            device[1].stop_all_notifies()

    def _find_connected_in_scanned(self):
        temp_devices = []
        for sc in self.scanned_devices:
            for cl in self.client_list:
                if sc.address == cl.address:
                    temp_devices.append(sc)
        return temp_devices

    async def scan(self):
        """ Scans all devices in advertisement mode and finds only chosen devices;
        makes sure no device is listed more than one time. Updates number of scanned devices"""

        self.scanned_devices = self._find_connected_in_scanned()
        logger.debug("Scanner on")
        async with BleakScanner() as scanner:
            await asyncio.sleep(5)
        for d in scanner.discovered_devices:
            if isinstance(d.name, str) and d.name.find(cr.SCAN_NAME) > -1:
                # logger.info(str(d.name) + " " + str(d.address))
                self.scanned_devices.append(d)
        self.nr_of_devices = len(self.scanned_devices)

    async def all_connect(self):
        """ Invokes connect function for all scanned devices.

        Raises:
            ValueError, Exception: error occurred when awaiting connecting single device
            """

        for x in self.scanned_devices:
            address = x.address
            try:
                await self.single_connect(address)
            except (ValueError, Exception):
                logger.error('Error while connecting to all devices on device: %s', address)

    async def all_disconnect(self):
        """ Invokes disconnect function for all connected devices. """

        for client in self.client_list:
            await self.single_disconnect(client.address)
        logger.debug("Ended disconnecting all devices")

    def _disconnect_callback(self, client: BleakClient) -> None:
        """ This function should be invoked when BleakClient is disconnect;

        Function might not be called if GUI uses asyncio and blocks Bleak threads.
        """

        for x in self.client_list:
            if x == client:
                self.client_list.remove(x)
        for device in self.client_device_list:
            if device[1].mac_ble == client.address:
                self.client_device_list.remove(device)
        logger.debug("disconnected callback from %s", client.address)

    async def _handler_single_connect(self, single_client: BleakClient):
        """ Handler for creating instances for connected BleakClient. """

        dev_class = None
        try:
            logger.debug("Single connected to: %s, type: %s",
                         single_client.address, type(single_client))
            _, data = await self.read_battery(single_client)
            logger.debug("Battery: %s", data)

            _, data = await self.read_dev_info(single_client)
            list_data = list(data)
            mac_ble_list = list_data[9:15]
            mac_wifi_list = list_data[30:36]

            _, data_conf = await self.read_config(single_client)
            logger.debug("Conf : %s", data_conf)

            is_already_client = False
            for client in self.client_list:
                if client.address == single_client.address:
                    is_already_client = True
                    for device in self.client_device_list:
                        if device[1].mac_ble == single_client.address:
                            is_already_client = True
                            dev_class = device
            if not is_already_client:
                dev_class = Device(single_client, mac_ble_list, mac_wifi_list)
                self.client_list.append(single_client)
                self.client_device_list.append([single_client, dev_class])
                if self.wifi_clients:
                    for wifi_client_list in self.wifi_clients:
                        mac_wifi_client = wifi_client_list[2]
                        if mac_wifi_client == dev_class.mac_wifi:
                            dev_class.client_wifi = wifi_client_list
            dev_class.configure = data_conf
        except Exception as e:
            logger.error("Can't set device: %s, reason: %s",
                         single_client.address, e)
            return None
        return dev_class


    async def single_connect(self, address):
        """ Creates and connects BleakClient.

        Creates and adds to list Device instance; if Wi-Fi client already exists,
        pairs up BleakClient wif Wi-Fi client inside Device instance.

        Args:
        address: str
            MAC address of BLE device to connect

        Returns:
            Tuple of BleakClient instance and Device instance corresponding to
            returned BleakClient instance.

        Raises:
            ValueError, Exception: error occurred when awaiting connecting
            single device or reading 2 characteristics.
        """
        ble_device = None
        for sc in self.scanned_devices:
            if address == sc.address:
                ble_device = sc
        if ble_device is None:
            single_client = BleakClient(address,
                                        disconnected_callback=self._disconnect_callback)
        else:
            single_client = BleakClient(ble_device,
                                        disconnected_callback=self._disconnect_callback)
        if single_client is not None:
            if not single_client.is_connected:
                try:
                    await single_client.connect()
                except (ValueError, Exception) as e:
                    logger.error("Can't connect: %s, reason: %s", address, e)
                    return [None, None]
                if single_client.is_connected:
                    dev_class = await self._handler_single_connect(single_client)
                    return single_client, dev_class
                logger.error('Failed to connect')
                return [None, None]
            if single_client.is_connected:
                logger.warning('Client already connected')
                # TODO: check if client is in list and if Device exists

    async def _handler_disconnecting(self, device_class, single_client):
        try:
            for device in self.client_device_list:
                device_address = device[1].mac_ble
                if device_address == single_client.address:
                    device_class = device[1]

            if single_client.is_connected:
                if device_class is not None:
                    logger.debug("Disconnecting device, %s", datetime.now())
                    device_class.stop_all_notifies()
                    await single_client.disconnect()
                    while single_client.is_connected:
                        continue
                    logger.debug('Disconnected single client: %s',
                                 str(single_client.address))
            else:
                # device_class.stop_all_notifies()
                self._disconnect_callback(single_client)
                logger.warning("Already disconnected: %s", single_client.address)
        except (ValueError, Exception) as e:
            logger.error('Error disconnecting to device, %s', e)
            raise Exception(e) from e

    async def single_disconnect(self, address):
        """ Disconnects BleakClient by address and destroys corresponding
        Device instance.

        Args:
            address: str
                MAC address of BLE device to disconnect

        Raises:
            ValueError, Exception: error occurred when awaiting disconnecting
            single device.
        """

        single_client = None
        device_class = None
        for client in self.client_list:
            if client.address == address:
                single_client = client
        if single_client is not None:
            await self._handler_disconnecting(device_class, single_client)

    # services
    async def read_config(self, client: BleakClient = None):
        """ Reads basic configuration of device by GATT characteristic.

        Args:
            client: BleakClient, optional:
                if exists, reads configuration from specified client;
                if it doesn't exist, reads configuration for all BLE clients

        Returns:
            list of MAC address and response from device or list of lists of
            MAC address and response from all clients.

        Raises:
            ValueError, Exception: error occurred when awaiting reading GATT
            service.
        """

        if client is None:
            clients = self.client_list
            response = []
            for cl in clients:
                if cl.is_connected:
                    address = cl.address
                    order, arr = self.chars.ble_config(action="R")
                    if order is not None:
                        try:
                            arr = await cl.read_gatt_char(order)
                            list_response = [address, list(arr)]
                            response.append(list_response)
                        except (ValueError, Exception) as e:
                            logger.error('Error: %s', e)
                else:
                    logger.warning("Client: %s not connected", cl.address)
            return response
        if client is not None:
            if client.is_connected:
                address = client.address
                order, arr = self.chars.ble_config(action="R")
                if order is not None:
                    try:
                        arr = await client.read_gatt_char(order)
                        response = [address, list(arr)]
                        return response
                    except (ValueError, Exception) as e:
                        logger.error('Error: %s', e)
            else:
                logger.warning("Client: %s not connected", client.address)

    async def _handler_single_w_config(self, client: BleakClient = None, **kwargs):
        if client.is_connected:
            order, arr = self.chars.ble_config(**kwargs,
                                               action="W")
            if order is not None and client:
                try:
                    await client.write_gatt_char(order, arr)
                    address = client.address
                    for device in self.client_device_list:
                        if device[0].address == address:
                            device[1].configure = arr
                except (ValueError, Exception) as e:
                    logger.error('Error writing: %s', e)
        else:
            logger.warning("Client: %s not connected", client.address)


    async def write_config(self,
                           client: BleakClient = None,
                           **kwargs):
        """ Writes basic configuration and reads same characteristic after.

        Writes basic configuration of device by GATT characteristic and reads
        same characteristic after.
        Sets list of parameters in Device instance corresponding to MAC address

        Args:
            kwargs
            client: BleakClient, optional

        Returns:
            list of MAC address and response from device or list of lists of MAC
            address and response from all clients.

        Raises:
            ValueError, Exception: error occurred when awaiting writing GATT
            service.
        """

        if client is None:
            clients = self.client_list
            for cl in clients:
                await self._handler_single_w_config(cl, **kwargs)
        if client is not None:
            await self._handler_single_w_config(client, **kwargs)

    async def write_action(self, action: int):
        """ Writes GATT characteristic for action of device.

        Args:
            action: int, optional

        Raises:
            ValueError, Exception: error occurred when awaiting writing
            GATT service.
        """
        i = 0
        clients = self.client_list
        for client in clients:
            if client.is_connected:
                if action == 4:
                    order, arr = self.chars.ble_set_action(action=action, master_slave=i)
                else:
                    order, arr = self.chars.ble_set_action(action=action)
                if order is not None and client:
                    try:
                        await client.write_gatt_char(order, arr)
                        if action == 4:
                            i += 1
                    except OSError as ee:
                        logger.error('Object closed error: %s', ee)
                    except (ValueError, Exception) as e:
                        logger.error('Error: %s', e)
            else:
                logger.warning("Client: %s not connected", client.address)

    async def read_wifi(self, client: BleakClient = None):
        """ Reads Wi-Fi configuration of device.

        Args:
            client: BleakClient, optional

        Returns:
            list of MAC address and response from device or list of lists of
            MAC address and response from all clients.

        Raises:
            ValueError, Exception: error occurred when awaiting reading GATT
            service.
        """

        if client is None:
            clients = self.client_list
            response = []
            for cl in clients:
                if cl.is_connected:
                    address = cl.address
                    order, arr = self.chars.ble_wifi_settings(action="R")
                    if order is not None:
                        try:
                            arr = await cl.read_gatt_char(order)
                            list_response = [address, list(arr)]
                            response.append(list_response)
                        except (ValueError, Exception) as e:
                            logger.error('Error: %s', e)
                else:
                    logger.warning("Client: %s not connected", cl.address)
            return response
        if client is not None:
            response = []
            if client.is_connected:
                address = client.address
                order, arr = self.chars.ble_wifi_settings(action="R")
                if order is not None:
                    try:
                        arr = await client.read_gatt_char(order)
                        response = [address, list(arr)]
                    except (ValueError, Exception) as e:
                        logger.error('Error: %s', e)
            else:
                logger.warning("Client: %s not connected", client.address)
            return response

    async def write_wifi(self,
                         ssid: str = cr.SSID,
                         psw: str = cr.PSW,
                         ip: list = None,
                         port: int = cr.PORT,
                         client: BleakClient = None):
        """ Writes Wi-Fi configuration to device.

        Args:
            ssid: str
            psw: str
            ip: list
            port: int
            client: BleakClient, optional

        Returns:
            If client is defined, returns 0 after completing successfully GATT
            writing.
            Returns -5 if value error or exception is caught.

        Raises:
            ValueError, Exception: error occurred when awaiting writing GATT
            service.
        """

        if ip is None:
            ip = cr.IP
        if not client:
            for cl in self.client_list:
                if cl.is_connected:
                    order, arr = self.chars.ble_wifi_settings(ssid=ssid,
                                                              psw=psw,
                                                              ip=ip,
                                                              port=port,
                                                              action="W")
                    if order is not None and cl:
                        try:
                            await cl.write_gatt_char(order, arr)
                        except (ValueError, Exception) as e:
                            logger.error('Error: %s', e)
                else:
                    logger.warning("Client: %s not connected", cl.address)
        else:
            if client.is_connected:
                order, arr = self.chars.ble_wifi_settings(ssid=ssid,
                                                          psw=psw,
                                                          ip=ip,
                                                          port=port,
                                                          action="W")
                if order is not None and client:
                    try:
                        await client.write_gatt_char(order, arr)
                        logger.debug("Written GATT")
                        return 0
                    except (ValueError, Exception) as e:
                        logger.error('Error: %s', e)
                        return -5
            else:
                logger.warning("Client: %s not connected", client.address)

    async def write_data_action(self, action: int = 0x00, data_type: int = 0x05):
        """ Writes data configuration for device.

        Args:
            action: int
            data_type: int

        Raises:
            ValueError, Exception: error occurred when awaiting writing GATT
            service.
        """

        clients = self.client_list
        for client in clients:
            if client.is_connected:
                order, arr = self.chars.ble_data_action(action=action, data_type=data_type)
                if order is not None and client:
                    try:
                        await client.write_gatt_char(order, arr)
                    except (ValueError, Exception) as e:
                        logger.error('Error: %s', e)
            else:
                logger.warning("Client: %s not connected", client.address)

    async def read_battery(self, client: BleakClient = None):
        """ Reads battery information from device.

        Args:
            client: BleakClient, optional

        Returns:
            list of MAC address and response from device or list of lists of
            MAC address and response from all clients.

        Raises:
            ValueError, Exception: error occurred when awaiting reading GATT
            service.
        """

        if client is None:
            clients = self.client_list
            response = []
            for cl in clients:
                if cl.is_connected:
                    address = cl.address
                    order, arr = self.chars.ble_battery()
                    if order is not None:
                        try:
                            arr = await cl.read_gatt_char(order)
                            list_response = [address, list(arr)]
                            response.append(list_response)
                        except (ValueError, Exception) as e:
                            logger.error('Error: %s', e)
                else:
                    logger.warning("Client: %s not connected", cl.address)
            return response
        if client is not None:
            response = []
            if client.is_connected:
                address = client.address
                order, arr = self.chars.ble_battery()
                if order is not None:
                    try:
                        arr = await client.read_gatt_char(order)
                        response = [address, list(arr)]
                    except (ValueError, Exception) as e:
                        logger.error('Error: %s', e)
            else:
                logger.warning("Client: %s not connected", client.address)
            return response

    async def read_id(self, client: BleakClient):
        """ Reads ID from device.

        Args:
            client: BleakClient

        Returns:
            list of MAC address and response from device.

        Raises:
            ValueError, Exception: error occurred when awaiting reading GATT
            service.
        """

        address = client.address
        response = []
        if client.is_connected:
            order, arr = self.chars.ble_device_id()
            if order is not None:
                try:
                    arr = await client.read_gatt_char(order)
                    response = [address, list(arr)]
                except (ValueError, Exception) as e:
                    logger.error('Error: %s', e)
        else:
            logger.warning("Client: %s not connected", address)
        return response

    async def read_name(self, client: BleakClient):
        """ Reads device name.

        Args:
            client: BleakClient

        Returns:
            list of MAC address and response from device.

        Raises:
            ValueError, Exception: error occurred when awaiting reading GATT
            service.
        """

        address = client.address
        response = []
        if client.is_connected:
            order, arr = self.chars.ble_device_name(action="R")
            if order is not None:
                try:
                    arr = await client.read_gatt_char(order)
                    response = [address, list(arr)]
                except (ValueError, Exception) as e:
                    logger.error('Error: %s', e)
        else:
            logger.warning("Client: %s not connected", address)
        return response

    async def write_name(self, client: BleakClient, name: str = None):
        """ Writes device name.

        Args:
            client: BleakClient
            name: str

        Raises:
            ValueError, Exception: error occurred when awaiting writing GATT
            service.
        """

        address = client.address
        if client.is_connected:
            order, arr = self.chars.ble_device_name(action="W", name=name)
            if order is not None:
                try:
                    await client.write_gatt_char(order, arr)
                except (ValueError, Exception) as e:
                    logger.error('Error: %s', e)
        else:
            logger.warning("Client: %s not connected", address)

    async def _handler_read_dev_info_single(self, client: BleakClient):
        """ Handler for extended info of single device. """

        if client is not None:
            response = []
            if client.is_connected:
                address = client.address
                order, arr = self.chars.ble_dev_info_new()
                if order is not None:
                    try:
                        arr = await client.read_gatt_char(order)
                    except BleakCharacteristicNotFoundError:
                        logger.warning('New not found, trying old')
                        order2, arr2 = self.chars.ble_dev_info_old()
                        if order is not None:
                            try:
                                arr2 = await client.read_gatt_char(order2)
                            except (ValueError, Exception) as e:
                                logger.error('Error on new and old (%s)', e)
                            else:
                                response = [address, list(arr2)]
                    except (ValueError, Exception) as e:
                        logger.error('Error on new: %s', e)
                    else:
                        response = [address, list(arr)]
            else:
                logger.warning("Client: %s not connected", client.address)
            return response

    async def _handler_read_dev_info_multiple(self):
        """ Handler for extended info of all devices. """

        clients = self.client_list
        response = []
        for cl in clients:
            if cl.is_connected:
                address = cl.address
                order, _ = self.chars.ble_dev_info_new()
                if order is not None:
                    try:
                        arr = await cl.read_gatt_char(order)
                    except BleakCharacteristicNotFoundError:
                        logger.warning('New not found, trying old')
                        order2, _ = self.chars.ble_dev_info_old()
                        if order is not None:
                            try:
                                arr2 = await cl.read_gatt_char(order2)
                            except (ValueError, Exception) as e:
                                logger.error('Error on new and old (%s)', e)
                            else:
                                list_response = [address, list(arr2)]
                                response.append(list_response)
                    except (ValueError, Exception) as e:
                        logger.error('Error on new: %s', e)
                    else:
                        list_response = [address, list(arr)]
                        response.append(list_response)
            else:
                logger.warning("Client: %s not connected", cl.address)
        return response

    async def read_dev_info(self, client: BleakClient = None):
        """ Reads extended info of device by GATT characteristic.

        Args:
            client: BleakClient, optional

        Returns:
            list of MAC address and response from device or list of lists of
            MAC address and response from all clients.

        Raises:
            ValueError, Exception: error occurred when awaiting reading GATT
            service.
        """

        if client is None:
            response = await self._handler_read_dev_info_multiple()
        else:
            response = await self._handler_read_dev_info_single(client)
        return response

    async def write_config_update(self,
                                  firmware: int,
                                  upd_nr: list = None,
                                  client: BleakClient = None):
        """ Writes update parameters.

        Args:
            firmware: int
            upd_nr: list
            client: BleakClient

        Returns:
            If client is defined and value error or exception is caught,
            returns -5.

        Raises:
            ValueError, Exception: error occurred when awaiting writing GATT
            service.
        """

        if not client:
            clients = self.client_list
            for cl in clients:
                if cl.is_connected:
                    order, arr = self.chars.ble_config_update(firmware=firmware,
                                                              upd_nr=upd_nr)
                    if order is not None and cl.is_connected:
                        try:
                            await client.write_gatt_char(order, arr)
                        except (ValueError, Exception) as e:
                            logger.error('Error: %s', e)
                else:
                    logger.warning("Client: %s not connected", cl.address)
        else:
            if client.is_connected:
                order, arr = self.chars.ble_config_update(firmware=firmware, upd_nr=upd_nr)
                if order is not None and client.is_connected:
                    try:
                        await client.write_gatt_char(order, arr)
                    except (ValueError, Exception) as e:
                        logger.error('Error: %s', e)
                        return -5
            else:
                logger.warning("Client: %s not connected", client.address)

    async def read_update_success(self, client: BleakClient):
        """ Reads update status.

        Args:
            client: BleakClient

        Returns:
            list of MAC address and response from device.

        Raises:
            ValueError, Exception: error occurred when awaiting reading GATT
            service.
        """

        response = []
        address = client.address
        if client.is_connected:
            order, arr = self.chars.ble_update_status(action="R")
            if order is not None and client.is_connected:
                try:
                    arr = await client.read_gatt_char(order)
                    response = [address, list(arr)]
                except (ValueError, Exception) as e:
                    logger.error('Error: %s', e)
                    return -5
        else:
            logger.warning("Client: %s not connected", client.address)
        return response
