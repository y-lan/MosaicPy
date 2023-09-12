

import openai


class ChatOpenAI:
    def __init__(self, system_prompt='You are an helpful assistant.',
                 model_name='gpt-3.5-turbo-16k', temperature=0.1):
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.temperature = temperature

    def complete(self, user_input,
                 temperature=None,
                 generate_n=1,
                 max_tokens=1024,
                 **kwargs):

        # if kwargs is not None, loop it to format the user_input
        if kwargs is not None:
            user_input = user_input.format(**kwargs)

        msgs = [{"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}]

        completion = openai.ChatCompletion.create(
            model=self.model_name,
            messages=msgs,
            max_tokens=max_tokens,
            n=generate_n,
            temperature=temperature if temperature is not None else self.temperature,
        )

        res = completion.choices

        if generate_n == 1:
            return res[0]['message']['content']
        else:
            return [r['message']['content'] for r in res]
