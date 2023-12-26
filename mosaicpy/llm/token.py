import json


def count_openai_token(text, encoding_name="cl100k_base"):
    import tiktoken

    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(text))
    return num_tokens


def estimate_request_tokens(msgs, tools=None):
    text = ""
    for msg in msgs:
        if isinstance(msg, dict):
            text += f"{msg.get('role')}:\n"
            if msg.get("tool_calls"):
                tool_calls = msg.get("tool_calls")
                for tool_call in tool_calls:
                    text += f"{tool_call.id} {tool_call.function.name}({tool_call.function.arguments})\n"
            if msg.get("content"):
                content = msg.get("content")
                if isinstance(content, list):
                    for content in content:
                        if content.get("type") == "text":
                            text += f"{content.get('text')}\n"
                else:
                    text += f"{content}\n"
        else:
            text += f"{msg.role}:\n"
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    text += f"{tool_call.function.name}({tool_call.function.arguments})\n"

        text += "\n"

    if tools:
        text += "Tools:\n"
        for tool in tools:
            func = tool.get("function")
            text += (
                f"{func['name']}:\n{func['description']}\n"
                + json.dumps(func.get("parameters"))
                + "\n"
            )

    return count_openai_token(text) + len(msgs) * 2


def estimate_response_tokens(completion):
    tokens = 0
    for choice in completion.choices:
        msg = choice.message

        if msg.content:
            tokens += count_openai_token(msg.content)
        else:
            for tool_call in msg.tool_calls:
                tokens += count_openai_token(tool_call.function.name + tool_call.function.arguments)
    return tokens
