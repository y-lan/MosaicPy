from mosaicpy.llm.chat import OpenAIBot


def main():
    bot = OpenAIBot(keep_conversation_state=True)

    while True:
        user_input = input("You (or 'exit' to quit): ")

        # Check if the user wants to exit
        if user_input.lower() == 'exit':
            print("Exiting the chat...")
            break

        try:
            # Get the response from the bot
            response = bot.chat(user_input)
            print("GPT:", response)
        except Exception as e:
            print("An error occurred:", e)


if __name__ == '__main__':
    main()
