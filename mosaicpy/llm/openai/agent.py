import base64
import json
import logging
import os
import time
import openai
import urllib
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from pydantic import BaseModel
from mosaicpy.collections import dict as mdict
from mosaicpy.llm.openai.function import build_function_signature
from mosaicpy.llm.openai.stream_aggregator import ChunkAggregator
from mosaicpy.llm.openai.tools import Tool
from mosaicpy.llm.prompt import replace_magic_placeholders
from mosaicpy.llm.token import count_openai_token, estimate_request_tokens, estimate_response_tokens
from mosaicpy.utils.event import SimpleEventManager
from mosaicpy.llm.schema import Event

from enum import Enum


logger = logging.getLogger(__name__)


def _create_image_content(image_path):
    parsed = urllib.parse.urlparse(image_path)

    if parsed.scheme in ('http', 'https'):
        return {
            "type": "image_url",
            "image_url": {
                "url": image_path
            },
        }
    elif os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                },
            }
    elif image_path.startswith("data:image/jpeg;base64,"):
        return {
            "type": "image_url",
            "image_url": {
                "url": image_path
            },
        }
    else:
        raise Exception(f"Invalid image path: {image_path}")


class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0


class AgentConfig(BaseModel):
    model_name: str = 'gpt-3.5-turbo-1106'
    system_prompt: str = 'You are a helpful assistant'
    temperature: float = 0.1
    keep_conversation_state: bool = False
    max_retry: int = 16
    timeout: int = 60
    stream: bool = False
    enable_magic_placeholders: bool = True
    execute_tools: bool = True
    verbose: bool = False
    support_tools: bool = True
    json_output: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.model_name in ('gpt-4-vision-preview'):
            self.support_tools = False

    class Config:
        arbitrary_types_allowed = True


class OpenAIAgent:
    def __init__(self, config: AgentConfig = None, tools: list[Tool] = None, **kwargs):

        if config is None:
            config = AgentConfig(**kwargs)
        self.config = config

        if config.verbose:
            logger.setLevel(logging.DEBUG)

        if tools is None:
            self.tools = {}
        else:
            self.tools = {tool.name: tool for tool in tools}

        self.conversation_state = []
        self.event_manager = SimpleEventManager()
        self.token_usage = TokenUsage()

    def subscribe(self, event, callback):
        if isinstance(event, str):
            event = Event[event.upper()]

        if event == Event.NEW_CHAT_TOKEN and not self.config.stream:
            logger.warning(
                "Event.NEW_CHAT_TOKEN is only available when stream=True")

        assert isinstance(
            event, Event), "event must be an instance of Event enum"
        self.event_manager.subscribe(event, callback)

    def add_ai_history(self, history_message):
        self.conversation_state.append(
            mdict(role='assistant', content=[
                  mdict(type='text', text=history_message)])
        )

    def add_user_history(self, history_message):
        self.conversation_state.append(
            mdict(role='user', content=[
                  mdict(type='text', text=history_message)])
        )

    def _get_system_msg(self):
        if self.config.enable_magic_placeholders:
            return {"role": "system", "content": replace_magic_placeholders(self.config.system_prompt)}
        else:
            return {"role": "system", "content": self.config.system_prompt}

    def _call_completion(self,
                         msgs, max_tokens, generate_n, temperature,
                         tools=None):
        kwargs = {
            "model": self.config.model_name,
            "messages": msgs,
            "max_tokens": max_tokens,
            "n": generate_n,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "timeout": self.config.timeout,
        }

        if self.config.support_tools and tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        if self.config.stream:
            kwargs['stream'] = True

        if self.config.json_output:
            kwargs['response_format'] = {"type": "json_object"}

        logger.debug(f'Request to OpenAI: {kwargs}')

        for _ in range(self.config.max_retry):
            try:
                completion = openai.chat.completions.create(**kwargs)
                break
            except openai.RateLimitError:
                time.sleep(2 ** _)
            except openai.APITimeoutError:
                pass
        else:
            raise Exception("Max retries exceeded")

        if self.config.stream:
            ca = ChunkAggregator(event_manger=self.event_manager)

            for chunk in completion:
                ca.update(chunk)

            completion = ca.to_chat_completion()

        estimated_usage_prompt = estimate_request_tokens(msgs, tools=tools)
        estimated_usage_completion = estimate_response_tokens(completion)

        logger.debug(
            f'Estimated token usage: prompt={estimated_usage_prompt}, completion={estimated_usage_completion}')

        if completion.usage:
            logger.debug(
                f'Actual token usage: prompt={completion.usage.prompt_tokens}, completion={completion.usage.completion_tokens}')
        else:
            completion.usage = CompletionUsage(
                completion_tokens=estimated_usage_completion,
                prompt_tokens=estimated_usage_prompt,
                total_tokens=estimated_usage_prompt + estimated_usage_completion
            )

        logger.debug(f'Response from OpenAI: {completion}')

        return completion

    def chat(self,
             user_input,
             image=None,
             temperature=None,
             max_tokens=1024,
             generate_n=1,
             **kwargs):

        # if kwargs is not None, loop it to format the user_input
        if kwargs:
            user_input = user_input.format(**kwargs)

        user_msg = {"role": "user", "content": [
            mdict(type='text', text=user_input)]}
        if image is not None:
            user_msg['content'].append(_create_image_content(image))

        msgs = [self._get_system_msg()]
        if self.config.keep_conversation_state:
            msgs.extend(self.conversation_state)
            self.conversation_state.append(user_msg)
        msgs.append(user_msg)

        tools = [build_function_signature(tool)
                 for tool in self.tools.values()]

        completion = self._call_completion(
            msgs, max_tokens, generate_n, temperature, tools=tools)

        if completion.choices[0].message.tool_calls:
            msgs.append(completion.choices[0].message)

            if self.config.execute_tools:
                for tool_call in completion.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    res = self.tools[function_name]._run(**function_args)
                    logger.info(
                        f'Tool call: {function_name}({function_args}) ->\n###\n{res}\n###')

                    msgs.append(mdict(
                        tool_call_id=tool_call.id,
                        role='tool',
                        name=function_name,
                        content=f'{res}'))
            else:
                res = []
                for tool_call in completion.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    res.append(
                        f'{function_name}({function_args})'
                    )

                print('\n'.join(res))
                return ''

            completion = self._call_completion(
                msgs, max_tokens, generate_n, temperature)

        res = completion.choices

        if generate_n == 1:
            res = res[0].message.content
        else:
            res = [r.message.content for r in res]

        if self.config.keep_conversation_state:
            self.conversation_state.append(
                mdict(role='assistant', content=[mdict(type='text', text=res)])
            )

        self.event_manager.publish(Event.FINISH_CHAT,
                                   prompt_tokens=completion.usage.prompt_tokens,
                                   completion_tokens=completion.usage.completion_tokens,
                                   response=res,)

        return res
