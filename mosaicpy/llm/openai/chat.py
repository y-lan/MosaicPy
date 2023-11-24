import base64
import json
import logging
import os
import time
import openai
import urllib

from pydantic import BaseModel
from mosaicpy.collections import dict as mdict
from mosaicpy.llm.openai.tools import Tool


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


TYPE_MAP = {
    int: "number",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "list",
    dict: "object",
    tuple: "object",
    set: "object",
    frozenset: "object",
    type(None): "null",
}


def build_function_signature(func: Tool):
    signature = {
        "name": func.name,
        "description": func.description,
    }

    params = func._run.__annotations__

    exclude_params = set(['return', 'run_manager'])

    signature["parameters"] = {
        "type": "object",
        "properties": {
            param: {
                "type": TYPE_MAP.get(type_),
                "description": "The " + param
            } for param, type_ in params.items() if param not in exclude_params
        },
        "required": [param for param in params if param not in exclude_params]
    }

    return {
        "type": "function",
        "function": signature
    }


class OpenAIBot:
    def __init__(self,
                 sys='You are a helpful assistant.',
                 model_name='gpt-3.5-turbo-16k',
                 temperature=0.1,
                 tools=None,
                 keep_conversation_state=False,
                 max_retry=16,
                 timeout=60):
        self.system_prompt = sys
        self.model_name = model_name
        self.temperature = temperature
        self.keep_conversation_state = keep_conversation_state
        self.conversation_state = []
        self.max_retry = max_retry
        self.timeout = timeout

        if tools is None:
            self.tools = {}
        else:
            self.tools = {tool.name: tool for tool in tools}

        self.token_usage = TokenUsage()

    def _get_system_msg(self):
        return {"role": "system", "content": self.system_prompt}

    def _call_completion(self, msgs, max_tokens, generate_n, temperature, tools=None):
        kwargs = {
            "model": self.model_name,
            "messages": msgs,
            "max_tokens": max_tokens,
            "n": generate_n,
            "temperature": temperature if temperature is not None else self.temperature,
            "timeout": self.timeout,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        logger.debug(f'Request to OpenAI: {kwargs}')

        for _ in range(self.max_retry):
            try:
                completion = openai.chat.completions.create(**kwargs)
                break
            except openai.RateLimitError:
                time.sleep(2 ** _)
            except openai.APITimeoutError:
                pass
        else:
            raise Exception("Max retries exceeded")

        self.token_usage.prompt += completion.usage.prompt_tokens
        self.token_usage.completion += completion.usage.completion_tokens

        logger.debug(f'Response from OpenAI: {completion}')

        return completion

    def chat(self,
             user_input,
             image=None,
             temperature=None,
             max_tokens=1024,
             generate_n=1,
             callback=None,
             **kwargs):

        # if kwargs is not None, loop it to format the user_input
        if kwargs is not None:
            user_input = user_input.format(**kwargs)

        user_msg = {"role": "user", "content": [
            mdict(type='text', text=user_input)]}
        if image is not None:
            user_msg['content'].append(_create_image_content(image))

        msgs = [self._get_system_msg()]
        if self.keep_conversation_state:
            msgs.extend(self.conversation_state)
        msgs.append(user_msg)

        tools = [build_function_signature(tool)
                 for tool in self.tools.values()]

        completion = self._call_completion(
            msgs, max_tokens, generate_n, temperature, tools)

        if completion.choices[0].message.tool_calls:
            msgs.append(completion.choices[0].message)
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

                completion = self._call_completion(
                    msgs, max_tokens, generate_n, temperature)

        res = completion.choices

        if generate_n == 1:
            res = res[0].message.content
            if callback is not None:
                res = callback(res)
        else:
            res = [r.message.content for r in res]
            if callback is not None:
                res = [callback(r) for r in res]

        if self.keep_conversation_state:
            self.conversation_state.extend([
                user_msg,
                mdict(role='assistant', content=[mdict(type='text', text=res)])
            ])

        return res