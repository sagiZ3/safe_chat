from gui import ChatUI
from server import Server
import tkinter as tk


def run_server():
    server = Server()
    server.receive_client()


def main():
    root = tk.Tk()
    app = ChatUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == '__main__':
    main()
