import google.generativeai as gen_ai  # delete - in different constants
import socket

from colorama import Fore  # delete?


# ================ Gemini Section ================  # delete - in different constants

GEMINI_API_KEY = "X"

def is_contain_profanity(payload):
    """ Checks if the payload contain any kind of profanity.
    :param payload: The user input
    :return: true if the payload contain profanity, false if it doesn't
    """

    gen_ai.configure(api_key=GEMINI_API_KEY)
    model = gen_ai.GenerativeModel("gemini-2.0-flash")
    chat = model.start_chat()

    prompt = f"הודעה לבדיקה: \"{payload}\", האם ההודעה מכילה קללות או ביטויים גסים? (כן/לא)"
    response = chat.send_message(prompt).text

    return "כן" in response

# ================ Gemini Section ================


LENGTH_FIELD_SIZE = 2
CONNECTION_PORT = 8888  # delete - in different constants
LISTEN_EVERYONE_IP = "0.0.0.0"  # delete - in different constants
LISTEN_LOOPBACK_IP = "127.0.0.1"  # delete - in different constants
SERVER_IP = socket.gethostbyname(socket.gethostname())  # delete - in different constants

BLOCKED_MACS_FILE_NAME = "blocked_macs.json"  # delete - in different constants
JSON_START_DATA = {"status_options": ["CLEAR", "WARNED", "BANED"], "blocked_macs": []}
WELCOME_MSG = "~~Welcome To Safe Chat~~"  # delete - in different constants
USERNAME_CONTAIN_PROFANITY_RESPONSE = "Please enter a name that doesn't include any kind of profanity!"  # delete - in different constants
EMPTY_USERNAME_RESPONSE = "Please enter a name!"  # delete - in different constants
COLOR = Fore.LIGHTBLUE_EX  # delete?
EXIT_COLOR = Fore.RED  # delete?


def create_msg(data) -> bytes:
    """Create a valid protocol message, with length field."""
    return f"{str(len(data)).zfill(LENGTH_FIELD_SIZE)}{data}".encode()


def get_msg(my_socket: socket.socket) -> tuple[bool, str]:
    """Extract message from protocol, without the length field.
       If length field does not include a number, returns False, "Error" """
    message = my_socket.recv(101).decode()  # TODO: add conversation option for getting data length
    payload_len = message[:LENGTH_FIELD_SIZE]
    payload = message[LENGTH_FIELD_SIZE:]

    if payload_len.isdigit() and int(payload_len) == len(payload):
        return True, payload

    return False, "Error"
