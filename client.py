import protocol
from protocol import is_contain_profanity,USERNAME_CONTAIN_PROFANITY_RESPONSE

import socket


class Client:
    def __init__(self):
        self._my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._my_socket.connect((protocol.SERVER_IP, protocol.PORT))
        self._nickname = ""
        self.messages_lst: list = []
        self.server_special_messages_dict = {"EXIT ": lambda: f"{self._nickname} left the chat!",
                                             "BAN_ACK ": lambda: "BAN_ACK "
                                            } # a space so that the client cannot imitate the message

    def is_username_includes_profanity(self, nickname) -> bool:
        if not is_contain_profanity(nickname):
            self._nickname = nickname
            self._my_socket.send(protocol.create_msg(self._nickname))
            return False
        return True

    def send_msg(self, payload):  # see if X window button include in the except statement - if at server it doesn't work
        client_msg = f"{self._nickname}: {payload}"
        if payload in self.server_special_messages_dict:
            client_msg = self.server_special_messages_dict[payload]()

        client_msg = protocol.create_msg(client_msg)
        self._my_socket.send(client_msg)


    def receive_msg(self):  # try needed?
        try:
            while True:
                valid_msg, msg = protocol.get_msg(self._my_socket)  # issue needed - ACK for EXIT
                if valid_msg:
                    self.messages_lst.append(msg)
                else:
                    self.messages_lst.append("Error! wrong protocol")
        except Exception as e:
            print("Error at receive_msg:", e)