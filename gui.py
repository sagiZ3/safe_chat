import tkinter as tk
import webbrowser
from threading import Thread
from tkinter import ttk
from tkinter import font

from client import Client
from protocol import EMPTY_USERNAME_RESPONSE, USERNAME_CONTAIN_PROFANITY_RESPONSE

# design colors
FRAME_BORDER_COLOR = "#7f5af0"
INNER_BG_COLOR = "#161b22"
ENTRY_BG = "#1f2937"
BTN_BG = "#7f5af0"
BTN_FG = "#ffffff"
TEXT_COLOR = "#e5e7eb"


class ChatUI:
    def __init__(self, root):
        self.client = None
        self._client_receive_thread = None
        self._root = root
        self._root.title("Safe Chat")
        self._root.configure(bg=FRAME_BORDER_COLOR)
        self._root.geometry("620x700")
        self._root.resizable(True, True)

        self._inner_frame = tk.Frame(root, bg=INNER_BG_COLOR)
        self._inner_frame.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)

        # Username
        self._username_var = tk.StringVar()
        self._username_locked = False

        username_frame = tk.Frame(self._inner_frame, bg=INNER_BG_COLOR)
        username_frame.pack(pady=(15, 5), padx=20, fill="x")

        tk.Label(username_frame, text="שם משתמש:", font=("Segoe UI", 10), fg=TEXT_COLOR, bg=INNER_BG_COLOR).pack(
            side="left")
        self._username_entry = tk.Entry(username_frame, textvariable=self._username_var, font=("Segoe UI", 10),
                                        bg=ENTRY_BG, fg=TEXT_COLOR, relief="flat")
        self._username_entry.pack(side="left", padx=10, fill="x", expand=True)

        self._set_username_btn = tk.Button(username_frame, text="✔", font=("Segoe UI", 10, "bold"), bg=BTN_BG,
                                           fg=BTN_FG,
                                           relief="flat", command=self.lock_username, cursor="hand2")
        self._set_username_btn.pack(side="left")

        # Chat zone - scrollbar etc..
        chat_frame = tk.Frame(self._inner_frame, bg=INNER_BG_COLOR)
        chat_frame.pack(padx=20, pady=(10, 0), fill="both", expand=True)

        self._text_widget = tk.Text(chat_frame, bg=ENTRY_BG, fg=TEXT_COLOR, font=("Segoe UI", 11),
                                    wrap="word", state="disabled", relief="flat", padx=10, pady=10)
        self._text_widget.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(chat_frame, command=self._text_widget.yview)
        scrollbar.pack(side="right", fill="y", padx=(4, 0))
        self._text_widget["yscrollcommand"] = scrollbar.set

        # Write line + button
        input_frame = tk.Frame(self._inner_frame, bg=INNER_BG_COLOR)
        input_frame.pack(fill="x", padx=20, pady=12)

        self._entry = tk.Entry(input_frame, font=("Segoe UI", 12), bg=ENTRY_BG, fg=TEXT_COLOR, relief="flat")
        self._entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
        self._entry.bind("<Return>", self.send_message)

        self._send_btn = tk.Button(input_frame, text="שלח", font=("Segoe UI", 11, "bold"), bg=BTN_BG, fg=BTN_FG,
                                   relief="flat", padx=14, pady=6, command=self.send_message, cursor="hand2")
        self._send_btn.pack(side="right")

    def lock_username(self):
        username = self._username_var.get().strip()
        if not username:
            self.show_temp_message(EMPTY_USERNAME_RESPONSE)
            return
        if not self.client:
            self.client = Client()  # creates the client object
            self._client_receive_thread = Thread(target=self.client.receive_msg)
            self._client_receive_thread.daemon = True
            self._client_receive_thread.start()
        if self.client.is_username_includes_profanity(username):
            self.show_temp_message(USERNAME_CONTAIN_PROFANITY_RESPONSE, show_time=4000)
            return

        self._username_entry.configure(state="disabled")
        self._set_username_btn.configure(state="disabled")
        self._username_locked = True
        self._root.after(300, self.check_for_available_messages)

    def send_message(self, event=None):
        if not self._username_locked:
            return  # disable sending a message without enter a username
        user_msg = self._entry.get().strip()
        if not user_msg:
            return
        self._entry.delete(0, tk.END)
        self._root.after(700, lambda: self.client.send_msg(user_msg))  # TODO: explain..

    def check_for_available_messages(self):
        while self.client.messages_lst:
            if self.client.messages_lst[0] == "BAN_SYN ":
                self._entry.config(state='disabled')
                self.show_temp_message("You've been banned from using the safe chat!", 0.5, 6000)
                self.client.send_msg("BAN_ACK ")
                self._root.after(6000, self._root.destroy)
            elif self.client.messages_lst[0] == "BANNED ":
                my_font = font.Font(family="Arial", size=100, weight="bold")
                link = tk.Label(self._root, text="!לחץ כאן", fg="blue", background=ENTRY_BG, cursor="hand2", font=my_font)
                link.pack(padx=20, pady=260)
                link.bind("<Button-1>", self.open_link)
                self.client.messages_lst.pop(0)
            else:
                self.display_message(self.client.messages_lst.pop(0))
        self._root.after(300, self.check_for_available_messages)

    def display_message(self, message):
        self._text_widget.configure(state="normal")
        self._text_widget.insert("end", f"{message}\n")
        self._text_widget.tag_add("user", "end-2l", "end-1l")
        self._text_widget.tag_configure("user", justify="right", foreground="#7f5af0", font=("Segoe UI", 12))
        self._text_widget.yview("end")
        if "/clear-chat$3" in message:
            self._text_widget.delete('1.0', tk.END)
        self._text_widget.configure(state="disabled")
        if "123S123" in message:
            for i in range(16):
                self.show_temp_message("LOL", rely=0.05 + 0.05 * i, show_time=800)

    def show_temp_message(self, message: str, rely=0.05, show_time=2000):
        temp_label = tk.Label(
            self._root,
            text=message,
            bg="#FFD966",  # background color
            fg="black",
            font=("Segoe UI", 12, "bold"), relief="solid",
            bd=1, padx=10, pady=5
        )

        temp_label.place(relx=0.5, rely=rely, anchor="n")  # label position
        temp_label.lift()
        self._root.after(show_time, temp_label.destroy)  # hides the message after 'show_time' seconds

    def on_close(self):
        if self._username_locked:
            try:
                self.client.send_msg("EXIT ")
                print("Client press the EXIT button")
            except ConnectionResetError:
                print(f"Error sending leave message:")
        self._root.after(1400, self._root.destroy)

    @staticmethod
    def open_link(event):
        webbrowser.open_new(r"https://miro.medium.com/1*BJArwUxopnCQlHkOhr5Mow.jpeg")
        webbrowser.open_new(r"https://lh3.googleusercontent.com/TDK5mKAE8VQtzrPoyGRNzgC5XQh-AC6Kgr-HdAQ06wsFZQRv-m6TsGY8cl4-RoLGuKeO_NYBsOPnydhvvp6g2p6Oeg=s1280-w1280-h800")
        