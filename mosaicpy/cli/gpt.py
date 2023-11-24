from mosaicpy.llm.openai.chat import OpenAIBot
from mosaicpy.llm.openai.tools import CalculatorTool

import logging
import fire
from colorama import init, Fore, Style

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


def print_ai(msg):
    print(Fore.MAGENTA + Style.BRIGHT + "GPT: " +
          msg + Style.RESET_ALL, end='\n')


logger = logging.getLogger('mosaicpy.llm')
logger.addHandler(ColorfulLogger())


def main(verbose: bool = False):
    if verbose:
        logger.setLevel(logging.DEBUG)

    bot = OpenAIBot(keep_conversation_state=True, tools=[CalculatorTool()])

    while True:
        try:
            user_input = input("You (or 'exit' to quit): ")
            # Check if the user wants to exit
            if user_input.lower() == 'exit':
                print("Exiting the chat...")
                break
        except KeyboardInterrupt:
            print("\nExiting the chat...")
            break

        try:
            # Get the response from the bot
            response = bot.chat(user_input)
            print_ai(response)
        except Exception as e:
            print("An error occurred:", e)
            if verbose:
                import traceback
                traceback.print_exc()


if __name__ == '__main__':
    fire.Fire(main)
