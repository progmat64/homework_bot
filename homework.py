import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException

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

logging.basicConfig(
    level=logging.DEBUG,
    filename="main.log",
    format="%(asctime)s, %(levelname)s, %(message)s, %(name)s",
)


def check_tokens():
    """Проверка доступности переменных окружения."""
    if (
        PRACTICUM_TOKEN is None
        or TELEGRAM_TOKEN is None
        or TELEGRAM_CHAT_ID is None
    ):
        logging.critical("Переменная окружения не определена!")
        raise NameError("Переменная окружения не определена!")


def send_message(bot, message):
    """Отправление сообщения в telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug("Сообщение успешно отправлено")
    except Exception as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    timestamp2 = timestamp or int(time.time())
    payload = {"from_date": timestamp2}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except RequestException as error:
        logging.error(error)

    if response.status_code != HTTPStatus.OK:
        raise RequestException(response)

    return response.json()


def check_response(response):
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


def parse_status(homework):
    """Извлечение информации о статусе работы."""
    if not homework.get("homework_name"):
        logging.error("Отсутствует имя домашней работы.")
        raise KeyError("Отсутствует ключ.")
    else:
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
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_status = ""

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)

            if len(homeworks) == 0:
                logging.debug("Ответ API пуст: нет домашних работ.")
                break
            for homework in homeworks:
                message = parse_status(homework)
                if message != last_status:
                    send_message(bot, message)
                    last_status = message

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            send_message(bot, message)
            exit()

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
