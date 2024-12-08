# -*- coding: utf-8 -*-
""" List of device's BLE UUIDs. """

import uuid

# here should be dictionary of UUIDs, which are empty due to privacy
UUID_DICT_TEMPLATE = {
    "ble_config": uuid.UUID(""),
    "ble_dev_info_old": uuid.UUID(""),
    "ble_set_action": uuid.UUID(""),
    "ble_get_status": uuid.UUID(""),
    "ble_wifi_settings": uuid.UUID(""),
    "ble_data_action": uuid.UUID(""),
    "ble_data": uuid.UUID(""),
    "ble_battery": uuid.UUID(""),
    "ble_device_id": uuid.UUID(""),
    "ble_device_name": uuid.UUID(""),
    "ble_dev_info_new": uuid.UUID(""),
    "ble_config_update": uuid.UUID(""),
    "ble_update_status": uuid.UUID(""),
    }