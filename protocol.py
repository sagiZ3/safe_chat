import socket
import google.generativeai as gen_ai  # delete - in different constants

from logging_config import logger


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

# ================================================


LENGTH_FIELD_SIZE = 3
CONNECTION_PORT = 8888  # delete - in different constants
LISTEN_EVERYONE_IP = "0.0.0.0"  # delete - in different constants
LISTEN_LOOPBACK_IP = "127.0.0.1"  # delete - in different constants
SERVER_IP = socket.gethostbyname(socket.gethostname())  # when run on the same network interface # delete - in different constants

CLIENTS_INFORMATION_FILE = "clients_information.json"  # delete - in different constants
JSON_START_DATA = {"status_options": ["CLEAR", "WARNED", "BANED"], "blocked_macs": []}
WELCOME_MSG = "~~Welcome To Safe Chat~~"  # delete - in different constants

USERNAME_CONTAIN_PROFANITY_RESPONSE = "Please enter a name that doesn't include any kind of profanity!"  # delete - in different constants
EMPTY_USERNAME_RESPONSE = "Please enter a name!"  # delete - in different constants
BANNED_MSG = r"https://miro.medium.com/1*BJArwUxopnCQlHkOhr5Mow.jpeg"
BANNED_MEME = r"https://lh3.googleusercontent.com/TDK5mKAE8VQtzrPoyGRNzgC5XQh-AC6Kgr-HdAQ06wsFZQRv-m6TsGY8cl4-RoLGuKeO_NYBsOPnydhvvp6g2p6Oeg=s1280-w1280-h800"


def build_segment(payload: str) -> bytes:
    """Creates a valid protocol message, with length field."""
    return f"{str(len(payload.encode())).zfill(LENGTH_FIELD_SIZE)}{payload}".encode('utf-8')


def send_segment(my_socket: socket.socket, payload: str) -> None:
    """
  Send a complete segment through the given socket.

    Ensures all bytes of the segment (built from payload) are sent, retrying
    until done. Handles connection reset or unexpected errors gracefully.

    :param my_socket: socket to send
    :param payload: string segment data
    :return: None
    """

    data = build_segment(payload)
    sent_to_buffer = 0

    while sent_to_buffer != len(data):
        try:
            sent_to_buffer += my_socket.send(data[sent_to_buffer:])
        except ConnectionResetError:
            logger.warning("The other side unexpectedly closed the connection; source: send_segment")
            break
        except Exception as e:
            logger.error(f"Unexpected ERROR at send_segment: {e}")
            break


def get_payload(my_socket: socket.socket) -> tuple[bool, str]:
    """Extract message from protocol, without the length field.
       If length field does not include a number, returns False, "Error" """

    try:
        encode_payload_len: str = my_socket.recv(LENGTH_FIELD_SIZE).decode('utf-8')  # will be always LENGTH_FIELD_SIZE because protocol puts it in the beginning of each message

        if encode_payload_len == "":  # means that the other side closed the connection
            logger.warning("The other side of the socket is closed!")
            return False, type(ConnectionAbortedError).__name__

        payload: str = my_socket.recv(int(encode_payload_len)).decode('utf-8')

        if encode_payload_len.isdigit() and int(encode_payload_len) == len(payload.encode()):
            return True, payload
    except ConnectionResetError as e:
        logger.warning("The other side unexpectedly closed the connection; source: get_payload")
        return False, type(e).__name__
    except Exception as e:
        logger.error(f"Unexpected ERROR at get_payload: {e}")
        return False, type(e).__name__

    return False, "Error"
