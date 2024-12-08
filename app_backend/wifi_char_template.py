# -*- coding: utf-8 -*-
""" Template methods for Wi-Fi characteristics. """


def file_characteristic(file_type=0x01, file_ver: list = None, file_size=0, crc32=0):  # W, 16 B
    """ Function handling file settings.

    Args:
        file_type: int
        file_ver: list
        file_size: int
        crc32: int
    Returns:
        list of bytes with information about file configuration.
    """

    if file_ver is None:
        file_ver = [1, 0, 0]
    header = "FILE"
    size = 16
    arr = bytearray(size)

    header_b = header.encode('ascii')
    file_ver_b = bytes(file_ver)
    file_size_b = file_size.to_bytes(4, 'little', signed=False)
    crc32_b = crc32.to_bytes(4, 'little', signed=False)

    # write arguments to array

    return arr


def chunk_characteristic(file_type=0x01,
                         packet_nr=0,
                         packet_size=0,
                         crc16=0,
                         data: bytearray = None):  # W, X+12 B
    """ Function handling chunk content.
    Args:
        file_type: int
        packet_nr: list
        packet_size: int
        crc16: int
        data: bytearray
    Returns:
        list of bytes with chunk content.
    """

    header = "CHUNK"
    data_len = len(data)
    size = 12 + data_len
    arr = bytearray(size)

    header_b = header.encode('ascii')
    packet_nr_b = packet_nr.to_bytes(2, 'little', signed=False)
    packet_size_b = packet_size.to_bytes(2, 'little', signed=False)
    crc16_b = crc16.to_bytes(2, 'little', signed=False)

    # write arguments to array

    return arr
