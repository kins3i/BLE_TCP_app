# -*- coding: utf-8 -*-
""" Module providing creating and handling TCP server. """

import select
import socket
import time
import threading

try:
    import credentials as cr
except ImportError:
    import credentials_template as cr

from logger_set import logger

from .parser import meas_data_parser



HOST = cr.HOST
PORT = cr.PORT


def calc_crc16(input_arr: bytes):
    """ Calculate CRC16 from array.

    Args:
        input_arr: bytes
            data to calculate crc16 from

    Returns:
        Calculated CRC.
    """

    crc = 0
    data_bytes = bytearray()
    for b in input_arr:
        data_bytes.append(b)
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


class WiFi:
    """ Class for creating and handle Wi-Fi servers and clients.

    Creates server, listens for clients and allows reading and writing
    to client's socket buffer. Server does keepAlive checks for idle clients.

    Attributes:
        client_flag: bool
        clients: list
        list_of_threads: list
        listening_clients: list
        dev_classes
        s: socket.socket

    Raises:
            ValueError, Exception: error occurred when creating and binding
            socket.
    """

    def __init__(self):
        self.client_flag = True
        self.server_flag = True
        self.clients = []
        self.list_of_threads = []
        self.listening_clients = []

        self.dev_classes = None

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            idle_time = int(0.5 * 1000)
            interval_time = int(0.5 * 1000)
            self.s.ioctl(socket.SIO_KEEPALIVE_VALS, (1, idle_time, interval_time))
            self.s.bind((HOST, PORT))
            logger.debug('Socket server created')
        except (ValueError, Exception) as e:
            logger.error('Error creating server')
            raise Exception(e) from e

    def create_server(self):
        """ Listens on socket for new clients.

        Listens for new clients. After catching client, reads header and
        creates connection with BLE client (if exists).
        If client got accepted on new port, every instance is updated.

        Raises:
            ValueError, Exception: error occurred when accepting new clients
            or parsing header.
        """

        self.s.listen(20)
        logger.debug("Server listening")
        ip_addr = None
        while self.server_flag:
            try:
                client, ip_addr = self.s.accept()
                data = client.recv(1024)
            except ConnectionError as e:
                logger.error('Client or server forced close on address: %s with error %s',
                             ip_addr, e)
            except TimeoutError as e:
                logger.error('Timeout error accepting client: %s with error %s', ip_addr, e)
            except (ValueError, Exception) as e:
                logger.error('Error listening on server >>create_server<<: %s', e)
                raise Exception(e) from e
            else:
                logger.debug("Connect: %s client: %s", ip_addr[:], client)
                if len(data) < 15:
                    output_str = "".join([chr(x) for x in data[0:6]])
                    output_mac = ":".join([format(x, '0>2X') for x in data[6:]])
                    logger.debug("Data: %s %s address %s", output_str, output_mac, ip_addr)
                    self._add_client(client, ip_addr, output_mac)
                else:
                    logger.debug("Data, bytes: %s address: %s", len(data), ip_addr)
        logger.debug("Closing server")

    def _add_client(self, client, ip_addr, output_mac,):
        if len(self.clients) > 0:
            for cli in self.clients:
                if cli[2] == output_mac:
                    self.clients.remove(cli)
        self.clients.append([client, ip_addr, output_mac])
        if self.dev_classes:
            for device in self.dev_classes:
                if output_mac == device[1].mac_wifi:
                    device[1].client_wifi = [client, ip_addr, output_mac]

    def listen_on_socket(self):
        """ Creates new thread for every eligible Wi-Fi client.

        Checks if client is already on listen. If not, starts new thread for
        client

        Raises:
            ValueError, Exception: error occurred when creating threads or
            checking existing threads.
        """

        try:
            for x in self.clients:
                client = x[0]
                addr = x[1]
                device = None
                is_listening = False
                for cli in self.listening_clients:
                    if cli == x:
                        is_listening = True
                if not is_listening:
                    for dev in self.dev_classes:
                        wifi_client = dev[1].client_wifi
                        if wifi_client[1] == addr:
                            device = dev[1]
                    if device is not None:
                        listening_thread = threading.Thread(target=self.on_new_client,
                                                            args=(client, addr, device),
                                                            daemon=True)
                        self.list_of_threads.append(listening_thread)
                        listening_thread.start()
                        self.listening_clients.append(x)
                        logger.debug("Listening thread: %s", addr)
                    else:
                        logger.warning("Device is none")
                else:
                    logger.warning("Client %s already on listen", addr)
        except (ValueError, Exception) as e:
            logger.error('Error listening on server >>listen_on_socket<<: %s', e)
        if not self.server_flag:
            logger.debug("Closing server")

    def on_new_client(self, conn, address, device=None):
        """ Listens and interprets data

        Listen on established socket buffer. Listens without blocking thread.
        If device is passed, gets configuration data for parsing received data.
        After catching connection error, removes client form list.
        Reacts with graceful and hard disconnect.

        Args:
            conn: socket.socket
                object to send and receive data
            address: tuple
                ip address and port received by client
            device: Device, optional
                instance of class with BLE and Wi-Fi client references

        Raises:
            ConnectionError: error occurred on connection between sockets.
            select.error: error occurred while waiting on data
            Exception: error occurred on parsing data.
        """

        while self.client_flag:
            try:
                ready, _, _ = select.select([conn], [], [], 5.0)
                if ready:
                    data = conn.recv(1024)
                    if data:
                        self._handler_data_receiver(data, address, device)
                    else:
                        logger.debug("Client disconnected")
                        break
                else:
                    continue

            except (ConnectionError, select.error) as err:
                if type(err).__name__ == ConnectionError:
                    logger.error("Caught connection error: %s", err)
                if type(err).__name__ == select.error:
                    logger.warning("Client or socket closed: %s", err)
                self._client_remover(address)
                break
            except Exception as e:
                logger.error("Client exception: %s", e)
                break
        logger.debug("Closing connection with client: %s", address)
        self._client_remover(address)
        logger.debug("End client listening")

    def _handler_data_receiver(self, data, address, device):
        """ Choose action based on length and header of data. """

        if len(data) < 15:
            output_str = "".join([chr(x) for x in data[0:6]])
            if output_str == "READY\x00":
                output_mac = ":".join([format(x, '0>2X') for x in data[6:]])
                logger.debug("Data >on_new_client<: %s %s address: %s",
                             output_str, output_mac, address)
            else:
                logger.debug("Data: %s address: %s", list(data), address)
        else:
            if device is not None and device.configure is not None:
                self._handler_data_parser(data, device)
            else:
                logger.debug("Data len: %s address: %s", len(data), address)

    @staticmethod
    def _handler_data_parser(data, device):
        """ Decode common data elements. """

        config = device.configure
        data_len = len(data) - 4 - 2 - 2
        header = "".join([chr(x) for x in data[0:4]])
        packet_len = int.from_bytes(data[4:6], 'little',
                                    signed=False)
        meas_data = data[6:6 + data_len]
        crc = int.from_bytes(data[-2:], 'little',
                             signed=False)

        crc_calc = calc_crc16(meas_data)

        packet_len_str = str(packet_len)
        crc_str = str(crc)

        battery = meas_data[-2:]
        if battery[0] > 5 or battery[0] < 5:
            if crc == crc_calc:
                # inp_str = (header + " " + packet_len_str + " " +
                # "<data>" + " " + crc_str +
                # ">" + str(crc_calc) + "<")
                meas_data_parser(meas_data, config, device.mac_ble)
            else:
                inp_str = (header + " " +
                           packet_len_str + " " +
                           "<data>" + " " +
                           crc_str + ">" +
                           str(crc_calc) + "<")
                logger.debug("Packet: %s", inp_str)

    def _client_remover(self, address):
        """ Helper method for removing client from list. """

        for client in self.clients:
            if address == client[1]:
                self.clients.remove(client)
                mac = client[2]
                for dev in self.dev_classes:
                    if mac == dev[1].mac_wifi:
                        dev[1].client_wifi.clear()

    def send_with_response(self, msg: bytearray, client = None):
        """ Sends data and waits for response

        Sends data to chosen client (or all available clients) and waits for
        client's sent data in response.

        Args:
            msg: bytearray
                data to send
            client: socket.socket
                client object to send and receive data

        Returns:
            client response or list of clients responses

        Raises:
            socket.error: error occurred when sending or receiving data.
        """

        if client is not None:
            try:
                client.send(msg)
            except socket.error:
                client.shutdown(2)
                # 0 = done receiving, 1 = done sending, 2 = both
                client.close()
            else:
                ready = select.select([client], [], [])
                if ready[0]:
                    response = client.recv(1024)
                    list_response = list(response)
                    return list_response
        else:
            for x in self.clients:
                client = x[0]
                try:
                    client.send(msg)
                except socket.error:
                    client.shutdown(2)
                    # 0 = done receiving, 1 = done sending, 2 = both
                    client.close()
                else:
                    ready = select.select([client], [], [])
                    if ready[0]:
                        response = client.recv(1024)
                        list_response = list(response)
                        return list_response
        return []

    @staticmethod
    def read_response(timeout=False, client = None):
        """ Reads data from client

        Reads data on demand with blocking or non-blocking way.
        Reads data from chosen client or all existing clients.

        Args:
            timeout: bool
                choose if thread will be blocked while waiting for data
            client: socket.socket
                client object to receive data

        Returns:
            client response or list of clients responses

        Raises:
            ConnectionError: error occurred on connection status between sockets.
            socket.error: error occurred when receiving data.
            Exception: error occurred while handling lists
        """

        if client is not None:
            if timeout:
                list_response = []
                try:
                    ready = select.select([client], [], [])
                    if ready[0]:
                        response = client.recv(1024)
                        list_response = list(response)
                except ConnectionError:
                    logger.error("Caught connection error")
                except socket.error as msg:
                    logger.error("Client or socket closed: %s", msg)
                except Exception as e:
                    logger.error("Client exception: %s", e)
                else:
                    return list_response
            else:
                response = client.recv(1024)
                list_response = list(response)
                return list_response
        return []

    def on_close(self):
        """ Gracefully joins clients' threads and closes server.

        Sets flags to graceful ending clients listening, joins clients threads
        and prints number of clients connected
        before closing server. Closes clients sockets.
        """

        self.client_flag = False
        self.server_flag = False
        time.sleep(1)
        threads = list(threading.enumerate()[::-1])
        for thread in threads:
            if "on_new_client" in thread.name:
                thread.join()
        logger.debug("Nr of clients: %s", len(self.clients))
        for client in self.clients:
            client[0].shutdown(2)
        for client in self.clients:
            client[0].close()
