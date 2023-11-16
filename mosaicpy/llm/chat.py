import base64
import os
import time
import openai
from openai.error import Timeout
import urllib
from mosaicpy.collections import dict as mdict


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
    else:
        raise Exception(f"Invalid image path: {image_path}")


class OpenAIBot:
    def __init__(self,
                 sys='You are a helpful assistant.',
                 model_name='gpt-3.5-turbo-16k',
                 temperature=0.1,
                 keep_conversation_state=False):
        self.system_prompt = sys
        self.model_name = model_name
        self.temperature = temperature
        self.keep_conversation_state = keep_conversation_state
        self.conversation_state = []

    def _get_system_msg(self):
        return {"role": "system", "content": self.system_prompt}

    def chat(self,
             user_input,
             image=None,
             temperature=None,
             max_tokens=1024,
             generate_n=1,
             callback=None,
             max_retry=16,
             timeout=60,
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

        for _ in range(max_retry):
            try:
                completion = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=msgs,
                    max_tokens=max_tokens,
                    n=generate_n,
                    temperature=temperature if temperature is not None else self.temperature,
                    timeout=timeout
                )
                break
            except openai.error.RateLimitError:
                time.sleep(2 ** _)
            except Timeout:
                pass
        else:
            raise Exception("Max retries exceeded")

        res = completion.choices

        if generate_n == 1:
            res = res[0]['message']['content']
            if callback is not None:
                res = callback(res)
        else:
            res = [r['message']['content'] for r in res]
            if callback is not None:
                res = [callback(r) for r in res]

        if self.keep_conversation_state:
            self.conversation_state.extend([
                user_msg,
                mdict(role='assistant', content=[mdict(type='text', text=res)])
            ])

        return res


if __name__ == "__main__":
    bot = OpenAIBot()

    while True:
        # Get input from the user
        user_input = input("Enter your message (or 'exit' to quit): ")

        # Check if the user wants to exit
        if user_input.lower() == 'exit':
            print("Exiting the chat...")
            break

        try:
            # Get the response from the bot
            response = bot.chat(user_input)
            print("Bot:", response)
        except Exception as e:
            print("An error occurred:", e)
