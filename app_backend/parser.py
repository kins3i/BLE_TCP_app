# -*- coding: utf-8 -*-
""" Accessory function for standardization of data parsing. """

from datetime import datetime
import struct

from logger_set import logger


def meas_data_parser(data, conf, device):
    """ Parse measurement data based on configuration.

    Args:
    data: list[int]
        data to parse
    conf: list[int]
        parameters to choose type of parser
    device: str
        MAC address of device (BLE)
    """

    if conf:
        arr = conf
        timestamp_option = arr[2]

        packet_nr = int.from_bytes(data[0:4], 'little', signed=False)
        battery = data[-2:]
        if timestamp_option == 0x00:
            data_obj = Data(data, conf)
            # timestamp, list_of_frames = data_obj.decode_data_packets()
            timestamp, _ = data_obj.decode_data_packets()
            print_str = (f"(DEVICE: {device}) Packet nr: {packet_nr}, "
                         f"battery: {battery[0]}, {battery[1]}; "
                         f"timestamp: {timestamp};")
            logger.info(print_str)
            return datetime.now(), device, print_str

        if timestamp_option == 0x01: # timestamp_option == 0x01:
            data_obj = Data(data, conf)
            # list_of_frames = data_obj.decode_data_frames()
            _ = data_obj.decode_data_frames()
            print_str = (f"Packet nr: {packet_nr}, battery: "
                         f"{battery[0]}, {battery[1]};")
            logger.info(print_str)
            return datetime.now(), device, print_str
    return datetime, device, ""


class Data:
    """ Handling data array."""

    def __init__(self, data, config):
        self.data = data
        self.timestamp_option = config[2]
        self.meas_number = config[3]

    # noinspection SpellCheckingInspection
    def decode_data_packets(self):
        """ Decoding data with timestamp for packet."""

        timestamp = int.from_bytes(self.data[4:8], 'little', signed=False)
        packet_data = self.data[8:-2]
        list_of_frames = []
        for i in range(self.meas_number):
            frame_data = packet_data[28 * i: 28 * (i + 1)]
            floats_frame = struct.unpack('<fffffff', frame_data)
            q0 = floats_frame[0]
            q1 = floats_frame[1]
            q2 = floats_frame[2]
            q3 = floats_frame[3]
            ax = floats_frame[4]
            ay = floats_frame[5]
            az = floats_frame[6]
            parsed_data = [q0, q1, q2, q3, ax, ay, az]
            list_of_frames.append(parsed_data)

        return [timestamp, list_of_frames]

    # noinspection SpellCheckingInspection
    def decode_data_frames(self):
        """ Decoding data with timestamp for every frame."""

        packet_data = self.data[4:-2]
        list_of_frames = []
        for i in range(self.meas_number):
            frame_data = packet_data[32 * i: 32 * (i + 1)]
            floats_frame = struct.unpack('<Ifffffff', frame_data)
            # timestamp = int.from_bytes(frame_data[0:4] ,'little', signed=False)
            timestamp = floats_frame[0]
            q0 = floats_frame[1]
            q1 = floats_frame[2]
            q2 = floats_frame[3]
            q3 = floats_frame[4]
            ax = floats_frame[5]
            ay = floats_frame[6]
            az = floats_frame[7]
            parsed_data = [timestamp, q0, q1, q2, q3, ax, ay, az]
            list_of_frames.append(parsed_data)

        return list_of_frames
