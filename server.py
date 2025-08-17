import socket
import threading
import os
import subprocess
import logging
import json
from time import sleep

import protocol
from protocol import is_contain_profanity, WELCOME_MSG


class Server:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self._server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self._server_socket.bind((protocol.LISTEN_EVERYONE_IP, protocol.CONNECTION_PORT))
        except Exception as e:
            logging.error("Failed to bind socket: " + str(e))
            exit()

        self._server_socket.listen()
        logging.info("=====Server is up and running=====")

        self._clients_data: dict = {}  # structure - client_socket: {"addr": addr, "nickname": nickname, "num_till_ban": num_till_ban)
        self.clients_information_data: None | dict[str, list[dict[str, any]]] = None
        self._arp_cache: dict[str: str] = {}  # structure: {IP: MAC}

        self._json_work_lock = threading.Lock()
        self._ensure_clients_information_file()
        self._update_clients_information_json()

    def receive_client(self):
        while True:
            client_socket, client_addr = self._server_socket.accept()
            try:
                valid_nickname, nickname = protocol.get_msg(client_socket)
            except ConnectionResetError:
                logging.warning("Client unexpectedly close the connection")
                client_socket.close()
            else:
                if valid_nickname:
                    self._clients_data[client_socket] = {"addr": client_addr, "nick": nickname, "num_till_ban": 0}
                    self._self_send(client_socket, WELCOME_MSG)
                    self._broadcast(f"{nickname} joined the chat!")
                    thread = threading.Thread(target=self._handle_client, args=(client_socket,))
                    thread.start()
                else:
                    self._self_send(client_socket, "Error with the nickname, please try again.")

    def _handle_client(self, client_socket) -> None:
        while True:
            try:
                print(self._clients_data)
                valid_msg, client_msg = protocol.get_msg(client_socket)
            except ConnectionResetError:
                logging.warning("Client unexpectedly close the connection")
                self._clients_data.pop(client_socket)
                client_socket.close()
                break
            if valid_msg:
                if client_msg == "BAN_ACK ":
                    self._clients_data.pop(client_socket)
                    client_socket.close()
                    break
                else:
                    if is_contain_profanity(client_msg):
                        self._broadcast(client_msg[:client_msg.find(':') + 2] + len(client_msg[client_msg.find(':') + 2:]) * '*')
                        self._clients_data[client_socket]['num_till_ban'] += 1
                        if self._clients_data[client_socket]['num_till_ban'] == 3:
                            self._self_send(client_socket, f"That's it!\n")
                            sleep(0.15)
                            self._broadcast(self._clients_data[client_socket]['nick'] + " has been permanently banned from using the safe chat, behave yourself!")
                            sleep(0.15)
                            self._self_send(client_socket, "BAN_SYN ")
                            # TODO: add file that keeps the client IP for ban forever
                        else:
                            self._self_send(client_socket, f"See Warning!\nYou have "
                                                          f"{3 - self._clients_data[client_socket]['num_till_ban']}"
                                                          f" more violations left before being banned")
                    else:
                        self._broadcast(client_msg)
            else:
                self._self_send(client_socket, "Error in message.")
                client_socket.recv(1024)  # Attempt to empty the socket from possible garbage

    def _ensure_clients_information_file(self) -> None:
        """ Creates a clients_information.json file if it doesn't exist
        and loads the JSON data into an accessible variable
        """

        if not os.path.exists(protocol.BLOCKED_MACS_FILE_NAME):
            with self._json_work_lock:
                with open(filename, "w") as f:  # type: ignore
                    json.dump(protocol.JSON_START_DATA, f, indent=4)  # type: ignore
                logging.info("New JSON file was created for blocking evil users 📁")

        with self._json_work_lock:
            with open(protocol.BLOCKED_MACS_FILE_NAME) as f:
                self.clients_information_data = json.load(f)  # Inserts the JSON data into an accessible variable
                logging.info("JSON file is now accessible!")

    def _extracts_user_mac_from_ip(self, ip: str) -> str:
        if ip in self._arp_cache:
            return self._arp_cache[ip]

        try:
            client_mac: str = subprocess.check_output(["arp", "-a", ip])\
                .decode().split(ip)[1].lstrip().split(" ")[0]  # no use of shell for preventing command injection
            self._arp_cache[ip] = client_mac
            logging.info("ARP cache just updated: " + str(self._arp_cache))
            return client_mac
        except Exception as e:
            logging.info("Problem with finding the client's MAC address: " + str(e))
            return ""  # TODO: consider in the check

    def _update_clients_information_json(self) -> None:  # need to make a server thread for updating JSON file frequently | Or update after every change
        """ Updates the JSON file (save data) from the accessible variable """

        with self._json_work_lock:
            with open(protocol.BLOCKED_MACS_FILE_NAME, "w+") as f:
                json.dump(self.clients_information_data, f, indent=4)  # type: ignore
                logging.info("JSON file were updated")

    def _is_user_blocked(self, client_ip: str) -> bool:
        for item in self.clients_information_data["clients_information"]:
            if item["mac"] == self._extracts_user_mac_from_ip(client_ip):
                if item["status"] == "BANED":
                    return True
                return False
        return False

    def _is_client_exist(self, client_ip: str) -> bool:
        """ Checks if the client were added to the JSON before and returns True | False accordingly """

        for item in self.clients_information_data["clients_information"]:
            if self._extracts_user_mac_from_ip(client_ip) == item["mac"]:
                return True
        return False

    def _add_client_data(self, client_ip: str) -> None:
        self.clients_information_data["clients_information"].append({
            "mac": self._extracts_user_mac_from_ip(client_ip),
            "past_warnings": 0,
            "status": "CLEAR"
        })
        self._update_clients_information_json()

    def _add_profanity_warning_and_update_status(self, client_ip: str) -> None:
        for item in self.clients_information_data["clients_information"]:
            if item["mac"] == self._extracts_user_mac_from_ip(client_ip):
                item["past_warnings"] += 1
                item["status"] = self._get_status_from_warnings(item["past_warnings"])
                self._update_clients_information_json()
                break

    def _broadcast(self, msg):
        for client_socket in self._clients_data.keys():
            client_socket.send(protocol.create_msg(msg))

    @staticmethod
    def _self_send(client_socket, msg):
        client_socket.send(protocol.create_msg(msg))

    @staticmethod
    def _get_status_from_warnings(past_warnings) -> str:
        if past_warnings == 0: return "CLEAR"
        if past_warnings == 3: return "BANNED"
        return "WARNED"

if __name__ == '__main__':
    server = Server()
    server.receive_client()
