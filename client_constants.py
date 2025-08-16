import socket

CONNECTION_PORT = 8888
SERVER_IP = socket.gethostbyname(socket.gethostname())  # change if run the client&server on different computers

USERNAME_CONTAIN_PROFANITY_RESPONSE = "Please enter a name that doesn't include any kind of profanity!"
EMPTY_USERNAME_RESPONSE = "Please enter a name!"
