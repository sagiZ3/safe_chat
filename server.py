import socket
import threading
import os
import subprocess
import json
from time import sleep
from select import select

import protocol
from protocol import is_contain_profanity, WELCOME_MSG
from logging_config import logger


class Server:
    def __init__(self):
        self._server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self._server_socket.bind((protocol.LISTEN_EVERYONE_IP, protocol.CONNECTION_PORT))
        except Exception as e:
            logger.error("Failed to bind socket: " + str(e))
            exit()

        self._server_socket.listen()
        logger.info("=====Server is up and running=====")

        self.__clients_data: dict = {}  # structure - client_socket: {client_socket: {"ip": ip, "nickname": nickname}
        self.__clients_information_data: None | dict[str, list[dict[str, any]]] = None
        self.__arp_cache: dict[str, str] = {}  # structure: {IP: MAC}

        self.__json_work_lock = threading.Lock()
        self.__ensure_clients_information_file()

    def clients_acceptor(self):
        while True:
            client_socket, client_addr = self._server_socket.accept()
            not_banned: bool = True
            try:
                valid_nickname, nickname = protocol.get_payload(client_socket)
            except ConnectionResetError:
                logger.warning("Client unexpectedly closed the connection")
                client_socket.close()
                continue

            # Initializes new client
            if valid_nickname:
                client_ip = client_addr[0]
                self.__clients_data[client_socket] = {"ip": client_ip, "nick": nickname}
                if self.__is_client_exist(client_ip):
                    if self.__is_user_blocked(client_ip):
                        self.__self_send(client_socket, "BANNED ")
                        not_banned = False
                else:
                    self.__add_client_data(client_ip)
                if not_banned:
                    self.__self_send(client_socket, WELCOME_MSG)
                    self.__broadcast(f"{nickname} joined the chat!")
                    thread = threading.Thread(target=self.__handle_client, args=(client_socket,))
                    thread.start()
            else:
                self.__self_send(client_socket, "Error with the nickname, please try again.")

    def __handle_client(self, client_socket) -> None:
        while True:
            try:
                logger.info(self.__clients_data)  # for logs using
                valid_msg, client_msg = protocol.get_payload(client_socket)
            except ConnectionResetError:
                logger.warning("Client unexpectedly closed the connection")
                self.__clients_data.pop(client_socket)
                client_socket.close()
                break
            except Exception as e:
                logger.warning(f"Unexpected Error occurred: {e}")
                self.__clients_data.pop(client_socket)
                client_socket.close()
                break

            if valid_msg:
                if client_msg == "BAN_ACK ":
                    self.__clients_data.pop(client_socket)
                    client_socket.close()
                    break
                elif is_contain_profanity(client_msg):
                    self.__broadcast(client_msg[:client_msg.find(':') + 2] + len(client_msg[client_msg.find(':') + 2:]) * '*')

                    if self.__adds_warning_and_return_updated_status(self.__clients_data[client_socket]["ip"]) == "BANNED":
                        self.__self_send(client_socket, f"That's it!\n")
                        sleep(0.05)
                        self.__broadcast(self.__clients_data[client_socket]['nick'] + " has been permanently banned from using the safe chat, behave yourself!")
                        sleep(0.15)
                        self.__self_send(client_socket, "BAN_SYN ")
                    else:
                        self.__self_send(client_socket, f"See Warning!\nYou have "
                                                      f"{3 - self.__get_current_past_warnings(self.__clients_data[client_socket]['ip'])}"
                                                      f" more violations left before being banned")
                else:
                    self.__broadcast(client_msg)
            else:
                self.__self_send(client_socket, "Error in message.")
                try:
                    logger.error(client_msg)
                    while True:
                        readable, _, _ = select([client_socket], [], [], 0)
                        if not readable:
                            break
                        client_socket.recv(1024)  # Attempt to empty the socket from possible garbage
                except ConnectionResetError:
                    logger.warning("Client unexpectedly closed the connection in a middle of reading data")
                    break
                except Exception as e:
                    logger.warning(f"Unexpected Error occurred: {e} ")

    def __ensure_clients_information_file(self) -> None:
        """ Creates a clients_information.json file if it doesn't exist
        and loads the JSON data into an accessible variable
        """

        if not os.path.exists(protocol.CLIENTS_INFORMATION_FILE):
            with self.__json_work_lock:
                with open(protocol.CLIENTS_INFORMATION_FILE, "w") as f:  # type: ignore
                    json.dump(protocol.JSON_START_DATA, f, indent=4)  # type: ignore
                logger.info("New JSON file was created for blocking evil users 📁")

        with self.__json_work_lock:
            with open(protocol.CLIENTS_INFORMATION_FILE) as f:
                self.__clients_information_data = json.load(f)  # Inserts the JSON data into an accessible variable
                logger.info("JSON file is now accessible!")

    def __extracts_user_mac_from_ip(self, ip: str) -> str:
        if ip in self.__arp_cache:
            return self.__arp_cache[ip]

        try:
            client_mac: str = subprocess.check_output(["arp", "-a", ip])\
                .decode().split(ip)[1].lstrip().split(" ")[0]  # no use of shell for preventing command injection
            self.__arp_cache[ip] = client_mac
            logger.info("ARP cache just updated: " + str(self.__arp_cache))
            return client_mac
        except Exception as e:
            logger.warning("Problem with finding the client's MAC address: " + str(e))
            return ""

    def __update_clients_information_json(self) -> None:  # need to make a server thread for updating JSON file frequently | Or update after every change
        """ Updates the JSON file (save data) from the accessible variable """

        with self.__json_work_lock:
            with open(protocol.CLIENTS_INFORMATION_FILE, "w") as f:
                json.dump(self.__clients_information_data, f, indent=4)  # type: ignore
                logger.info("JSON file were updated")

    def __is_user_blocked(self, client_ip: str) -> bool:
        for item in self.__clients_information_data["clients_information"]:
            if item["mac"] == self.__extracts_user_mac_from_ip(client_ip):
                return item["status"] == "BANNED"
        return False

    def __is_client_exist(self, client_ip: str) -> bool:
        """ Checks if the client were added to the JSON before and returns True | False accordingly """

        for item in self.__clients_information_data["clients_information"]:
            if self.__extracts_user_mac_from_ip(client_ip) == item["mac"]:
                return True
        return False

    def __add_client_data(self, client_ip: str) -> None:
        self.__clients_information_data["clients_information"].append({
            "mac": self.__extracts_user_mac_from_ip(client_ip),
            "past_warnings": 0,
            "status": "CLEAR"
        })
        self.__update_clients_information_json()

    def __adds_warning_and_return_updated_status(self, client_ip: str) -> str:
        for item in self.__clients_information_data["clients_information"]:
            if item["mac"] == self.__extracts_user_mac_from_ip(client_ip):
                item["past_warnings"] += 1

                new_status = self.__get_status_from_warnings(item["past_warnings"])
                item["status"] = new_status

                self.__update_clients_information_json()
                return new_status
        return "CLEAR"

    def __get_current_past_warnings(self, client_ip) -> int:
        for item in self.__clients_information_data["clients_information"]:
            if item["mac"] == self.__extracts_user_mac_from_ip(client_ip):
                return item["past_warnings"]
        return 0

    def __broadcast(self, msg):
        for client_socket in self.__clients_data.keys():
            protocol.send_segment(client_socket, msg)

    @staticmethod
    def __self_send(client_socket, msg):
        protocol.send_segment(client_socket, msg)

    @staticmethod
    def __get_status_from_warnings(past_warnings) -> str:
        if past_warnings == 0: return "CLEAR"
        if past_warnings >= 3: return "BANNED"  # also bigger because clients can open several gui on the same machine
        return "WARNED"


if __name__ == '__main__':
    server = Server()
    server.clients_acceptor()
