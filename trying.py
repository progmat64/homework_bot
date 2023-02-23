"""
from pprint import pprint

import requests  # для запроса к серверу
from telegram import Bot  # для создания бота
from telegram import ReplyKeyboardMarkup  # класс клавиатуры
from telegram.ext import CommandHandler  # проверка обновлений на сервере
from telegram.ext import Filters, MessageHandler, Updater

url = "https://practicum.yandex.ru/api/user_api/homework_statuses/"  # адрес API
headers = {
    "Authorization": "OAuth y0_AgAAAAARfJB5AAYckQAAAADcSaYSk-dE_AUSQiKDtuO_H4inC2JeBs4"
}  # токен авторизации
payload = {"from_date": 0}  # временная метка

homework_statuses = requests.get(url, headers=headers, params=payload)
home = homework_statuses.json()["homeworks"][0]["status"]
pprint(home)
if home == "approved":
    print("Yes!")

TELEGRAM_TOKEN = "6127767137:AAExiP1hCRHIYiU-xV0mfbsUsevTR3DRviE"

# сделать так, чтобы на каждое сообщение отвечал привет!
# вероятно использовать updater dispatcher для перенаправления команд и функций
chat_id = 1091301077
text = "Привет, давай летать!"
# bot = Bot(token=TELEGRAM_TOKEN)
# bot.send_message(chat_id, text)

# print(bot.get_chat(chat_id))
# print(bot.get_updates())


updater = Updater(token=TELEGRAM_TOKEN)
# print(updater)


def say_hi(update, context):
    chat = update.effective_chat
    print(update)
    name = update.message.chat.first_name
    context.bot.send_message(chat_id=chat.id, text=f"Привет {name}")


# Для обработки каждого типа сообщений используется свой хэндлер
# класс Filters() может отфильтровывать сообщения разных типов


def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    # Вот она, наша кнопка.
    # Обратите внимание: в класс передаётся список, вложенный в список,
    # даже если кнопка всего одна.
    button = ReplyKeyboardMarkup([["Показать фото котика"]], resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat.id,
        text="Спасибо, что вы включили меня, {}!".format(name),
        # Добавим кнопку в содержимое отправляемого сообщения
        reply_markup=button,
    )


updater.dispatcher.add_handler(CommandHandler("start", wake_up))

updater.dispatcher.add_handler(MessageHandler(Filters.text, say_hi))


updater.start_polling(
    poll_interval=2
)  # Запускает опрос обновлений из Telegram. poll_interval - проверка обновлений раз в 600 секунд
updater.idle()  # Бот будет работать до тех пор, пока не нажмете Ctrl-C
"""
