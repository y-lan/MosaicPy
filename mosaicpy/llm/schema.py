from enum import Enum


class Event(Enum):
    NEW_CHAT_TOKEN = 1
    USE_TOOL = 2
    FINISH_CHAT = 3
