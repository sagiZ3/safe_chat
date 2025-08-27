import tkinter as tk

from gui import ChatUI


def main():
    root = tk.Tk()
    app = ChatUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == '__main__':
    main()
