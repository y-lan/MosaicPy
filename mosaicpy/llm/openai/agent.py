import base64
import json
import logging
import os
import time
import openai
import urllib
from openai import AzureOpenAI
from openai.types import CompletionUsage

from mosaicpy.collections import dict as mdict
from mosaicpy.llm import Agent
from mosaicpy.llm.openai.function import build_function_signature
from mosaicpy.llm.openai.stream_aggregator import ChunkAggregator
from mosaicpy.llm.openai.tools import Tool
from mosaicpy.llm.prompt import replace_magic_placeholders
from mosaicpy.llm.schema import (
    BaseConfig,
    ChatResponse,
    SimpleMessage,
    TokenUsage,
)
from mosaicpy.llm.token import estimate_request_tokens, estimate_response_tokens


logger = logging.getLogger(__name__)


def _create_image_content(image_path):
    parsed = urllib.parse.urlparse(image_path)

    if parsed.scheme in ("http", "https"):
        return {
            "type": "image_url",
            "image_url": {"url": image_path},
        }
    elif os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            return {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
    elif image_path.startswith("data:image/jpeg;base64,"):
        return {
            "type": "image_url",
            "image_url": {"url": image_path},
        }
    else:
        raise Exception(f"Invalid image path: {image_path}")


class AgentConfig(BaseConfig):
    model_name: str = "gpt-3.5-turbo-0125"
    frequency_penalty: float = 0
    use_azure: bool = False
    azure_endpoint: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.model_name in ["gpt-4-vision-preview"]:
            self.support_tools = False


class OpenAIAgent(Agent):
    ROLE_SYSTEM = "system"

    def __init__(self, config: AgentConfig = None, tools: list[Tool] = None, **kwargs):
        if config is None:
            config = AgentConfig(**kwargs)

        super().__init__(config=config, tools=tools, **kwargs)

        if config.verbose:
            logger.setLevel(logging.DEBUG)

    def _get_client(self):
        if self.config.use_azure:
            assert (
                os.environ["AZURE_OPENAI_API_KEY"] is not None
            ), "AZURE_OPENAI_API_KEY must be provided"
            assert self.config.azure_endpoint is not None, "Azure endpoint must be provided"
            return AzureOpenAI(
                api_version="2023-07-01-preview",
                azure_endpoint=self.config.azure_endpoint,
            )
        else:
            return openai

    def _get_system_msg(self):
        if self.config.enable_magic_placeholders:
            return SimpleMessage.from_text(
                self.ROLE_SYSTEM, replace_magic_placeholders(self.config.system_prompt)
            )
        else:
            return SimpleMessage.from_text(self.ROLE_SYSTEM, self.config.system_prompt)

    def _assemble_request_messages(self, user_contents):
        msgs = [self._get_system_msg()]
        if self.config.keep_conversation_state:
            msgs.extend(self.conversation_state)

        msgs.append(SimpleMessage(role=self.ROLE_USER, content=user_contents))
        return msgs

    def _call_completion(self, msgs, max_tokens, generate_n, temperature, tools=None):
        kwargs = {
            "model": self.config.model_name,
            "messages": msgs,
            "max_tokens": max_tokens or self.config.max_tokens,
            "n": generate_n,
            "temperature": temperature or self.config.temperature,
            "frequency_penalty": self.config.frequency_penalty,
            "top_p": self.config.top_p,
            "seed": self.config.seed,
            "timeout": self.config.timeout,
        }

        if self.config.support_tools and tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        if self.config.stream:
            kwargs["stream"] = True

        if self.config.json_output:
            kwargs["response_format"] = {"type": "json_object"}

        logger.debug(f"Request to OpenAI: {kwargs}")

        for _ in range(self.config.max_retry):
            try:
                client = self._get_client()
                completion = client.chat.completions.create(**kwargs)
                break
            except openai.RateLimitError:
                if self.config.verbose:
                    logger.warning(f"Rate limit exceeded. Retrying in {2 ** _} seconds...")
                time.sleep(2**_)
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
            f"Estimated token usage: prompt={estimated_usage_prompt}, completion={estimated_usage_completion}"
        )

        if completion.usage:
            logger.debug(
                f"Actual token usage: prompt={completion.usage.prompt_tokens}, completion={completion.usage.completion_tokens}"
            )
        else:
            completion.usage = CompletionUsage(
                completion_tokens=estimated_usage_completion,
                prompt_tokens=estimated_usage_prompt,
                total_tokens=estimated_usage_prompt + estimated_usage_completion,
            )

        logger.debug(f"Response from OpenAI: {completion}")

        return completion

    def chat(
        self,
        user_input,
        image=None,
        full_response=False,
        temperature=None,
        max_tokens=None,
        **kwargs,
    ):
        # if kwargs is not None, loop it to format the user_input
        if kwargs:
            user_input = user_input.format(**kwargs)

        user_contents = [mdict(type="text", text=user_input)]
        if image is not None:
            user_contents.append(_create_image_content(image))
        msgs = self._assemble_request_messages(user_contents)

        tools = [build_function_signature(tool) for tool in self.tools.values()]

        completion = self._call_completion(msgs, max_tokens, 1, temperature, tools=tools)

        if completion.choices[0].message.tool_calls:
            msgs.append(completion.choices[0].message)

            if self.config.execute_tools:
                for tool_call in completion.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    res = self.tools[function_name]._run(**function_args)
                    logger.info(f"Tool call: {function_name}({function_args}) ->\n###\n{res}\n###")

                    msgs.append(
                        mdict(
                            tool_call_id=tool_call.id,
                            role="tool",
                            name=function_name,
                            content=f"{res}",
                        )
                    )
            else:
                res = []
                for tool_call in completion.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    res.append(f"{function_name}({function_args})")

                print("\n".join(res))
                return ""

            completion = self._call_completion(msgs, max_tokens, 1, temperature)

        response = ChatResponse(
            content=completion.choices[0].message.content,
            model=self.config.model_name,
            finish_reason=completion.choices[0].finish_reason,
            usage=TokenUsage(
                prompt=completion.usage.prompt_tokens,
                completion=completion.usage.completion_tokens,
            ),
            input_contents=user_contents,
        )

        self.event_manager.publish_finish_chat(response)

        return response if full_response else response.content
