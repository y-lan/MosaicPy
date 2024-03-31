from functools import partial
from mosaicpy.llm import get_agent
from mosaicpy.llm.openai.agent import OpenAIAgent
from mosaicpy.llm.openai.tools import CalculatorTool

import logging
import fire
from colorama import init, Fore, Style

from mosaicpy.llm.schema import Event

init()


class ColorfulLogger(logging.StreamHandler):
    def emit(self, record):
        log_level = record.levelno
        if log_level == logging.DEBUG:
            color = Fore.CYAN
        elif log_level == logging.INFO:
            color = Fore.GREEN
        elif log_level == logging.WARNING:
            color = Fore.YELLOW
        elif log_level == logging.ERROR:
            color = Fore.RED
        elif log_level == logging.CRITICAL:
            color = Fore.RED + Style.BRIGHT
        else:
            color = Fore.WHITE
        record.msg = color + str(record.msg) + Style.RESET_ALL
        super(ColorfulLogger, self).emit(record)


def print_ai(msg, prefix="GPT: ", end="\n"):
    print(Fore.MAGENTA + Style.BRIGHT + prefix + msg + Style.RESET_ALL, end=end)


logger = logging.getLogger("mosaicpy.llm")
logger.addHandler(ColorfulLogger())


def main(provider="openai", stream: bool = True, verbose: bool = False):
    if verbose:
        logger.setLevel(logging.DEBUG)

    bot = get_agent(
        provider,
        stream=stream,
        keep_conversation_state=True,
        verbose=verbose,
        tools=[CalculatorTool()],
    )
    name = "GPT" if provider == "openai" else "Claude"

    if stream:
        bot.on_new_chat_token(lambda content: print_ai(content, prefix="", end=""))
        bot.on_finish_chat(lambda response: print_ai("", prefix="", end="\n"))
    else:
        bot.on_finish_chat(lambda response: print_ai(response.content, prefix=""))

    while True:
        try:
            user_input = input("You (or 'exit' to quit): ")
            if user_input.lower() == "exit":
                print("Exiting the chat...")
                break
            elif user_input.strip() == "":
                continue
        except KeyboardInterrupt:
            print("\nExiting the chat...")
            break

        try:
            print_ai("", prefix=f"{name}: ")
            bot.chat(user_input)
        except Exception as e:
            print("An error occurred:", e)
            if verbose:
                import traceback

                traceback.print_exc()


if __name__ == "__main__":
    fire.Fire(main)
