from enum import Enum
from typing import Optional
from mosaicpy.collections import dict as mdict

from pydantic import BaseModel, ConfigDict


class BaseConfig(BaseModel):
    model_name: str
    system_prompt: str = "You are a helpful assistant"

    # LLM
    temperature: float = 0
    top_p: float = 1
    seed: int = None
    max_tokens: int = 1024

    # system
    json_output: bool = False
    keep_conversation_state: bool = False
    max_retry: int = 16
    timeout: int = 60
    stream: bool = False
    enable_magic_placeholders: bool = True
    verbose: bool = False

    # tools
    execute_tools: bool = True
    support_tools: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())


class SimpleMessage(BaseModel):
    role: str
    content: list
    tool_calls: Optional[list[dict]] = None

    @staticmethod
    def from_text(role, text):
        return SimpleMessage(role=role, content=[mdict(type="text", text=text)])


class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0

    def update(self, usage):
        self.prompt += usage.prompt
        self.completion += usage.completion


class Event(Enum):
    NEW_CHAT_TOKEN = 1
    USE_TOOL = 2
    FINISH_CHAT = 3


class ChatResponse(BaseModel):
    content: str
    model: str
    finish_reason: str
    usage: TokenUsage
    input_contents: list[dict]
