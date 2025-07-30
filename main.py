from gui import ChatUI
from server import Server
import tkinter as tk
from threading import Thread


def run_server():
    server = Server()
    server.receive_clients()


def main():
    # server_thread = Thread(target=run_server)  # runs the server on a separate thread
    # server_thread.daemon = True
    # server_thread.start()

    root = tk.Tk()
    app = ChatUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == '__main__':
    main()
