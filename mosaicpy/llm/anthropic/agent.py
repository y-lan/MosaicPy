import base64
import imghdr
import logging
import mimetypes
import os
from typing import Any
from anthropic import Anthropic
from mosaicpy.collections import dict as mdict
import urllib

from anthropic.types import (
    ContentBlockDeltaEvent,
    ContentBlockStartEvent,
    ContentBlockStopEvent,
    Message,
    MessageDeltaEvent,
    MessageStartEvent,
    MessageStopEvent,
)
from mosaicpy.llm import Agent
from mosaicpy.llm.prompt import replace_magic_placeholders
from mosaicpy.llm.schema import (
    BaseConfig,
    ChatResponse,
    SimpleMessage,
    TokenUsage,
)

logger = logging.getLogger(__name__)


def _create_image_block(data: str, media_type: str = "image/jpeg"):
    return mdict(type="image", source=mdict(type="base64", media_type=media_type, data=data))


def _create_image_content(image_path):
    if image_path.startswith("data:image/jpeg;base64,"):
        return _create_image_block(image_path.split(",")[1])

    parsed = urllib.parse.urlparse(image_path)

    if parsed.scheme in ("http", "https"):
        mime_type, _ = mimetypes.guess_type(image_path)
        with urllib.request.urlopen(image_path) as response:
            base64_image = base64.b64encode(response.read()).decode("utf-8")
            return _create_image_block(base64_image, mime_type or "image/jpeg")

    elif os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            image_type = imghdr.what(image_path)
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            return _create_image_block(base64_image, f"image/{image_type}")

    raise Exception(f"Invalid image path: {image_path}")


def _assemble_chat_response(msg: Message, user_contents: list[dict]):
    return ChatResponse(
        content=msg.content[0].text,
        model=msg.model,
        finish_reason="completed",
        usage=TokenUsage(prompt=msg.usage.input_tokens, completion=msg.usage.output_tokens),
        input_contents=user_contents,
    )


class AgentConfig(BaseConfig):
    model_name: str = "claude-3-haiku-20240307"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class AnthropicAgent(Agent):
    def __init__(self, config: Any = None, tools: list[Any] = None, api_key=None, **kwargs):
        if config is None:
            config = AgentConfig(**kwargs)
        super().__init__(config=config, tools=tools, **kwargs)

        if config.verbose:
            logger.setLevel(logging.DEBUG)

        self._client = Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
        )

    def _get_system_msg(self):
        if self.config.enable_magic_placeholders:
            return replace_magic_placeholders(self.config.system_prompt)
        else:
            return self.config.system_prompt

    def _assemble_request_messages(self, user_contents):
        msgs = []
        if self.config.keep_conversation_state:
            msgs.extend(self.conversation_state)

        msgs.append(SimpleMessage(role=self.ROLE_USER, content=user_contents))

        return msgs

    def _handle_stream(self, stream):
        message = None
        for event in stream:
            if isinstance(event, MessageStartEvent):
                message = Message(
                    id=event.message.id,
                    model=event.message.model,
                    role=event.message.role,
                    type="message",
                    content=[],
                    usage=event.message.usage,
                )
            elif isinstance(event, ContentBlockStartEvent):
                message.content.append(event.content_block)
            elif isinstance(event, ContentBlockDeltaEvent):
                delta_text = event.delta.text
                self.event_manager.publish_new_chat_token(delta_text)
                message.content[-1].text += delta_text
            elif isinstance(event, ContentBlockStopEvent):
                pass
            elif isinstance(event, MessageDeltaEvent):
                message.usage.output_tokens = event.usage.output_tokens
            elif isinstance(event, MessageStopEvent):
                pass

        return message

    def chat(
        self,
        user_input,
        image=None,
        return_all=False,
        temperature=None,
        max_tokens=None,
        **kwargs,
    ):
        if kwargs:
            user_input = user_input.format(**kwargs)
        user_contents = [mdict(type="text", text=user_input)]
        if image is not None:
            user_contents.append(_create_image_content(image))

        messages = self._assemble_request_messages(user_contents)

        res = self._client.messages.create(
            model=self.config.model_name,
            system=self._get_system_msg(),
            max_tokens=max_tokens or self.config.max_tokens,
            messages=messages,
            stream=self.config.stream,
        )

        message = None
        if self.config.stream:
            message = self._handle_stream(res)
        else:
            message = res

        response = _assemble_chat_response(message, user_contents)
        self.event_manager.publish_finish_chat(response)

        return response if return_all else response.content
