# -*- coding: utf-8 -*-
""" Template methods for BLE characteristics. """

from logger_set import logger
from .uuid_dict_template import UUID_DICT_TEMPLATE


class Characteristics:
    """ Class creating arrays for UUIDs. """

    def __init__(self):
        # UUID_DICT is a dictionary with keys written inside methods;
        # values for keys are device dependent and are not shown due
        # to privacy reason
        self.__uuid_dict = UUID_DICT_TEMPLATE.copy()

    def ble_config(self, *,
                   odr: int = 56,
                   timestamp: int = 0x00,
                   nr_of_meas: int = 10,
                   dmp: int = 0x01,
                   transmission: int = 0x00,
                   odr_div: int = 0,
                   power_mode: int = 0x00,
                   time_ble: int = 0x00,
                   time_wifi: int = 0x00,
                   action: str = None):  # R/W, 10 B
        """ Config characteristic. """

        order = self.__uuid_dict['ble_config']
        size = 10
        # size = 8
        arr = bytearray(size)

        logger.debug("Order ble config(%s), %s", action, order)

        if action is not None:
            if action == "R":
                return [order, arr]
            if action == "W":

                # write arguments to array

                return [order, arr]
        return []

    def ble_dev_info_old(self):  # R, 46 B
        """ Old full info characteristic. """

        order = self.__uuid_dict['ble_dev_info_old']
        size = 46
        arr = bytearray(size)

        logger.debug("Order ble_dev_info_old(R): %s", order)

        return [order, arr]

    def ble_set_action(self, master_slave: int = 0, action: int = 2):  # W, 10 B
        """ Action characteristic. """

        order = self.__uuid_dict['ble_set_action']
        size = 10
        arr = bytearray(size)

        logger.debug("Order ble_set_action(W): %s", order)

        # write arguments to array

        return [order, arr]

    @staticmethod
    def _set_bit(value: int, index: int, boolean: bool = True):
        """Set the index:th bit of v to 1 if x is truthy, else to 0, and return the new value."""
        mask = 1 << index  # Compute mask, an integer with just bit 'index' set.
        value &= ~mask  # Clear the bit indicated by the mask (if x is False)
        if boolean:
            value |= mask  # If x was True, set the bit indicated by the mask.
        return value  # Return the result, we're done.

    def ble_get_status(self):  # N, 10 B
        """ Device state and report characteristic. """

        order = self.__uuid_dict['ble_get_status']
        size = 10
        arr = bytearray(size)

        logger.debug("Order ble_get_status(N): %s", order)

        return [order, arr]

    def ble_wifi_settings(self, ssid: str = "", psw: str = "", ip: list = None, port: int = 8088,
                          action: str = None):  # R/W, 80 B
        """ Wi-Fi config characteristic. """

        if ip is None:
            ip = [1, 2, 3, 4]
        order = self.__uuid_dict['ble_wifi_settings'].hex
        size = 80
        arr = bytearray(size)

        logger.debug("Order ble_wifi_settings(%s), %s", action, order)

        if action is not None:
            if action == "R":  # receive bytes
                return [order, arr]
            if action == "W":

                # write arguments to array

                return [order, arr]
        return []

    def ble_data_action(self, action=0x00, data_type=0x05):  # W, 10 B
        """ Action control characteristic. """

        order = self.__uuid_dict['ble_data_action']
        size = 3
        arr = bytearray(size)

        logger.debug("Order ble_data_action(W): %s, action: %s", action, order)

        # write arguments to array

        return [order, arr]

    def ble_data(self):  # N, up to 40 B
        """ Data characteristic. """

        order = self.__uuid_dict['ble_data']
        size = 40
        arr = bytearray(size)

        logger.debug("Order ble_data(N): %s", order)

        return [order, arr]

    def ble_battery(self):  # R, 2 B
        """ Battery state characteristic. """

        order = self.__uuid_dict['ble_battery']
        size = 2
        arr = bytearray(size)

        logger.debug("Order ble_battery(R): %s", order)

        return [order, arr]

    def ble_device_id(self):  # R, 20 B // W, 20 B with password
        """ Serial and short info characteristic. """

        order = self.__uuid_dict['ble_device_id']
        size = 20
        arr = bytearray(size)

        logger.debug("Order ble_device_id(R): %s", order)

        return [order, arr]

    def ble_device_name(self, action: str = None, name: str = None):  # R/W, 20 B
        """ Device name characteristic. """

        order = self.__uuid_dict['ble_device_name']
        size = 20
        arr = bytearray(size)

        if action is not None:
            logger.debug("Order ble_device_name(%s), %s", action, order)
            if action == "R":
                return [order, arr]

            if action == "W":

                # write arguments to array

                return [order, arr]
        return []

    def ble_dev_info_new(self):  # R, 46 B
        """ New full info characteristic. """

        order = self.__uuid_dict['ble_dev_info_new']
        size = 46
        arr = bytearray(size)

        logger.debug("Order ble_dev_info_new(R): %s", order)

        return [order, arr]

    def ble_config_update(self, firmware: int = 0x03, upd_nr: list = None):  # W, 4 B
        """ Update config characteristic. """

        if upd_nr is None:
            upd_nr = [1, 0, 0]
        order = self.__uuid_dict['ble_config_update']
        size = 4
        arr = bytearray(size)

        # write arguments to array

        logger.debug("Order ble_config_update(W):, %s data: %s", order, list(arr))

        return [order, arr]

    def ble_update_status(self, action: str = None):  # N, R, 2 B
        """ Update status characteristic. """

        order = self.__uuid_dict['ble_update_status']
        size = 2
        arr = bytearray(size)

        if action == "N":
            logger.debug("Order ble_update_status(N): %s", order)
        elif action == "R":
            logger.debug("Order ble_update_status(R): %s", order)

        return [order, arr]
