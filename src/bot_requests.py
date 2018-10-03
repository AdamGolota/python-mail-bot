import requests, telegram, config
bot = telegram.Bot(config.token)
chat_id = config.chat_id

def sendMessage(text) :
    bot.send_message(chat_id=chat_id, text=text, disable_notification=True)


def sendDocument(files) :
    bot.send_document(chat_id=chat_id, document=files, disable_notification=True)
