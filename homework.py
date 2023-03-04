import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exception import ResponcePracticumError

load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens() -> bool:
    """Проверка доступности переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправление сообщения в telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug("Сообщение отправлено")
    except telegram.TelegramError as error:
        logging.error(f"Сбой в работе программы: {error}")
    else:
        logging.debug("Сообщение отправлено. Ошибка на стороне telegram")


def get_api_answer(timestamp: int) -> dict:
    """Запрос к эндпоинту API-сервиса."""
    timestamp = timestamp or int(time.time())
    payload = {"from_date": timestamp}

    try:
        logging.info(f"Запрос к API, эндпоинт {ENDPOINT}, параметр {HEADERS}")
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise ResponcePracticumError(error)

    if response.status_code != HTTPStatus.OK:
        raise requests.RequestException(response)

    return response.json()


def check_response(response: dict) -> list:
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        logging.error("Имеет некорректный тип.")
        raise TypeError("Имеет некорректный тип.")

    if "homeworks" not in response:
        logging.error("Отсутствует ожидаемый ключ в ответе.")
        raise KeyError("Отсутствует ожидаемый ключ в ответе.")

    if not isinstance(response.get("homeworks"), list):
        logging.error("Имеет некорректный тип.")
        raise TypeError("Имеет некорректный тип.")

    return response["homeworks"]


def parse_status(homework) -> str:
    """Извлечение информации о статусе работы."""
    if not homework.get("homework_name"):
        logging.error("Отсутствует имя домашней работы.")
        raise KeyError("Отсутствует ключ.")
    homework_name = homework.get("homework_name")

    if "status" not in homework:
        logging.error("Отсутствует ключ.")
        raise KeyError("Отсутствует ключ.")

    homework_status = homework.get("status")
    verdict = HOMEWORK_VERDICTS.get(homework_status)

    if homework_status not in HOMEWORK_VERDICTS:
        logging.error("Отсутствует ключ.")
        raise KeyError("Отсутствует ключ.")

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical("Переменная окружения не определена!")
        sys.exit("Переменная окружения не определена!")

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_status = ""

    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get("current_date")
            homeworks = check_response(response)

            if homeworks:
                message = parse_status(homeworks[0])
                if message != last_status:
                    send_message(bot, message)
                    last_status = message
            else:
                logging.debug("Ответ API пуст: нет домашних работ.")
                send_message(bot, "Нет домашних работ")

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message)
            send_message(bot, message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        filename="main.log",
        format="%(asctime)s, %(levelname)s, %(message)s, %(name)s",
    )
    main()
