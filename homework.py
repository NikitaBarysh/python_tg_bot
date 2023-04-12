import os
import time
import requests
import logging
import sys
from dotenv import load_dotenv
from http import HTTPStatus
import exception
import telegram.ext

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка на наличие всех переменных окружения."""
    if (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID) is not None:
        return True


def send_message(bot, message):
    """Отправялет сообщение в Telegram чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except Exception:
        logging.error('Не удалось отправить сообщений в Telegram')
        raise telegram.error.TelegramError()  # Не мог поставить эту ошибку
    else:  # в except, т к не проходили бы тесты
        logging.debug('Сообщение в Telegram отправлено')


def get_api_answer(timestamp):
    """Делает запрос к ENDPOINT и возвращает ответ API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=payload)
    except requests.exceptions.HTTPError('Ошибка статуса'):
        raise exception.UnexpectedStatusError('Неожиданный статус')
    if response.status_code != HTTPStatus.OK:
        raise exception.UnavailableServer('Сайт недоступен')
    response = response.json()
    return response


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logging.error('Тип данных ответа не словарь!')
        raise TypeError('Ответ вернулся не словарём!')
    try:
        response['homeworks']
    except ValueError('Отсутствие значения homeworks'):
        logging.debug('Нет обновлений в ДЗ')
    homework = response['homeworks']
    current_date = response['current_date']
    try:
        (homework and current_date)
    except KeyError('Какой-то ключи отсутствует'):
        logging.error('Отсутствует один из ключей response')
    if not isinstance(homework, list):
        raise TypeError('homework не является списком!')
    return homework


def parse_status(homework):
    """Проверка полученной домашней работы."""
    try:
        homework_name = homework['homework_name']
    except KeyError('homework_name'):
        logging.error('Проблема с ключом homework_name')
    status = homework.get('status')
    STATUS = ['reviewing', 'approved', 'rejected']
    if status not in STATUS:
        logging.error('Неожиданный статус ДЗ')
        raise exception.UnexpectedStatusError('Неожиданный статус ДЗ')
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутвует токен')
        sys.exit('Отсутствует токен')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_mes = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response.get('homeworks')
            if len(homeworks) == 0:
                logging.debug('Отсутсвует статус работы')
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
            timestamp = response.get('current_data', timestamp)
        except exception.UnexpectedStatusError():
            logging.error(
                'Сбой в работе программы: Эндпоинт недоступен.'
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            if message != last_mes:
                send_message(bot, message)
                message = last_mes
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
