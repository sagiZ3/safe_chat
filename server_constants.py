import google.generativeai as gen_ai


CONNECTION_PORT = 8888
LISTEN_EVERYONE_IP = "0.0.0.0"
LISTEN_LOOPBACK_IP = "127.0.0.1"

BLOCKED_MACS_FILE_NAME = "clients_information.json"  # delete - in different constants
JSON_START_DATA = {"status_options": ["CLEAR", "WARNED", "BANED"], "blocked_macs": []}
WELCOME_MSG = "~~Welcome To Safe Chat~~"

# ================ Gemini Section ================

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