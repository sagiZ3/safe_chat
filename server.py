import protocol
from protocol import is_contain_profanity, WELCOME_MSG
from time import sleep

import socket
import threading



class Server:
    def __init__(self):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(("0.0.0.0", protocol.PORT))
        self._server_socket.listen()
        self._clients_dict = {}  # structure - client_socket: {"addr": addr, "nickname": nickname, "num_till_ban": num_till_ban)

    def receive_clients(self):
        while True:
            client_socket, client_addr = self._server_socket.accept()
            try:
                valid_nickname, nickname = protocol.get_msg(client_socket)
            except ConnectionResetError:
                print("Client unexpectedly close the connection")
                client_socket.close()
            else:
                if valid_nickname:
                    self._clients_dict[client_socket] = {"addr": client_addr, "nick": nickname, "num_till_ban": 0}
                    self.self_send(client_socket, WELCOME_MSG)
                    self.broadcast(f"{nickname} joined the chat!")
                    thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                    thread.start()
                else:
                    self.self_send(client_socket, "Error with the nickname, please try again.")


    def handle_client(self, client_socket) -> None:
        while True:
            try:
                print(self._clients_dict)
                valid_msg, client_msg = protocol.get_msg(client_socket)
            except ConnectionResetError:
                print("Client unexpectedly close the connection")
                self._clients_dict.pop(client_socket)
                client_socket.close()
                break
            if valid_msg:
                if client_msg == "BAN_ACK ":
                    self._clients_dict.pop(client_socket)
                    client_socket.close()
                    break
                else:
                    if is_contain_profanity(client_msg):
                        self.broadcast(client_msg[:client_msg.find(':')+2] + len(client_msg[client_msg.find(':')+2:]) * '*')
                        self._clients_dict[client_socket]['num_till_ban'] += 1
                        if self._clients_dict[client_socket]['num_till_ban'] == 3:
                            self.self_send(client_socket, f"That's it!\n")
                            sleep(0.15)
                            self.broadcast(self._clients_dict[client_socket]['nick'] + " has been permanently banned from using the safe chat, behave yourself!")
                            sleep(0.15)
                            self.self_send(client_socket, "BAN_SYN ")
                            # TODO: add file that keeps the client IP for ban forever
                        else:
                            self.self_send(client_socket, f"See Warning!\nYou have "
                                                          f"{3 - self._clients_dict[client_socket]['num_till_ban']}"
                                                          f" more violations left before being banned")
                    else:
                        self.broadcast(client_msg)
            else:
                self.self_send(client_socket, "Error in message.")
                client_socket.recv(1024)  # Attempt to empty the socket from possible garbage


    @staticmethod
    def self_send(client_socket, msg):
        client_socket.send(protocol.create_msg(msg))

    def broadcast(self, msg):
        for client_socket in self._clients_dict.keys():
            client_socket.send(protocol.create_msg(msg))


if __name__ == '__main__':
    server = Server()
    server.receive_clients()