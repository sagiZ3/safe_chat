import socket

import protocol
from protocol import is_contain_profanity
from logging_config import logger


class Client:
    def __init__(self):
        self.my_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.connect((protocol.SERVER_IP, protocol.CONNECTION_PORT))
        self._nickname: str = ""
        self.messages_lst: list = []
        self.__client_commands = {"EXIT ": lambda: f"{self._nickname} left the chat!",
                                             "BAN_ACK ": lambda: "BAN_ACK ",
                                             "BANNED ": lambda: "BANNED "  # lambda uses for customise the nickname every time
                                  }  # a space so that the client cannot imitate the message

    def is_username_includes_profanity(self, nickname) -> bool:  # need to be deleted - cannot give the client access to the API!
        if not is_contain_profanity(nickname):
            self._nickname = nickname
            protocol.send_segment(self.my_socket, self._nickname)
            return False
        return True

    def send_msg(self, payload) -> None:

        client_msg = f"{self._nickname}: {payload}"

        if payload in self.__client_commands:
            client_msg = self.__client_commands[payload]()

        protocol.send_segment(self.my_socket, client_msg)

    def receive_msg(self) -> None:
        try:
            while True:
                valid_msg, msg = protocol.get_payload(self.my_socket)
                if valid_msg:
                    self.messages_lst.append(msg)
                else:
                    self.messages_lst.append("Error! wrong protocol")
        except Exception as e:
            logger.warning("Unexpected ERROR at receive_msg:", e)
