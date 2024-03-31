from abc import ABC, abstractmethod
import logging
from typing import Any, Optional, Union

from mosaicpy.collections import dict as mdict
from mosaicpy.llm.schema import BaseConfig, ChatResponse, Event, SimpleMessage, TokenUsage
from mosaicpy.utils.event import SimpleEventManager

logger = logging.getLogger(__name__)


class LLMEventManager(SimpleEventManager):
    def on_new_chat_token(self, callback):
        self.subscribe(Event.NEW_CHAT_TOKEN, lambda data: callback(data["content"]))

    def publish_new_chat_token(self, content: str):
        self.publish(Event.NEW_CHAT_TOKEN, content=content)

    def on_finish_chat(self, callback):
        self.subscribe(
            Event.FINISH_CHAT,
            lambda data: callback(data["response"]),
        )

    def publish_finish_chat(self, repsponse: ChatResponse):
        self.publish(Event.FINISH_CHAT, response=repsponse)


class Agent(ABC):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    def __init__(self, config: BaseConfig, tools: list[Any], **kwargs):
        self.config = config

        if isinstance(tools, list):
            tools = {tool.name: tool for tool in tools}
        elif not isinstance(tools, dict):
            tools = {}
        self.tools = tools

        self.token_usage = TokenUsage()
        self.conversation_state = []
        self.event_manager = LLMEventManager()

        def on_finish_chat(response: ChatResponse):
            self.token_usage.update(response.usage)
            self.conversation_state.append(
                SimpleMessage(role=self.ROLE_USER, content=response.input_contents)
            )
            self.conversation_state.append(
                SimpleMessage.from_text(self.ROLE_ASSISTANT, response.content)
            )

        self.on_finish_chat(on_finish_chat)

    def get_token_usage(self) -> TokenUsage:
        return self.token_usage

    def on_new_chat_token(self, callback):
        if not self.config.stream:
            logger.warning("Event.NEW_CHAT_TOKEN is only available when stream=True")
        self.event_manager.on_new_chat_token(callback)

    def on_finish_chat(self, callback):
        self.event_manager.on_finish_chat(callback)

    def _add_history(self, role, content):
        if not self.config.keep_conversation_state:
            return

        if isinstance(content, str):
            message = mdict(role=role, content=[mdict(type="text", text=content)])
        elif isinstance(content, list):
            message = mdict(role=role, content=content)
        self.conversation_state.append(message)

    def add_ai_history(self, history_message):
        self._add_history(self.ROLE_ASSISTANT, history_message)

    def add_user_history(self, history_message):
        self._add_history(self.ROLE_USER, history_message)

    @abstractmethod
    def _assemble_request_messages(self, user_contents):
        pass

    @abstractmethod
    def chat(
        self,
        user_input: str,
        image: Optional[str] = None,
        return_all: bool = False,
        temperature: Optional[float] = None,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Union[str, ChatResponse]:
        """
        Process a chat input, potentially including an image, and return the response.
        """
        pass


def get_agent(agent_type: str, **kwargs):
    if agent_type == "openai":
        from mosaicpy.llm.openai.agent import OpenAIAgent

        return OpenAIAgent(**kwargs)
    elif agent_type == "anthropic":
        from mosaicpy.llm.anthropic.agent import AnthropicAgent

        return AnthropicAgent(**kwargs)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
