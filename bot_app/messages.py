import asyncio
import logging

from aiogram.types import Message
from aiogram.types.base import Integer
import logs.confs.log_conf

from bot_app.app import bot
from bot_app.keyboards import STOP_TIMER

BOT_APP_LOG = logging.getLogger('bot_app_log')

# text templates

COMMANDS = '/help \n/balance \n/get_sim'

WELCOME_MESSAGE = '''
Привет, это бот, который поможет тебе получить виртуальный номер\n
Для начала работы, укажи свой API-ключ\n\n
/send_api_key - отправить свой API-ключ\n
/help - чтобы лучше разобраться в том, для чего этот бот\n'''

HELP_MESSAGE = '''
Данный телеграм-бот был создан для упрощенного получения виртуальных номеров, 
которые можно регистрировать в определенных сервисах, например, в приложениях 
по доставке продуктов. Для этого он использует API сайта sms-activate.ru\n\n
Чтобы сайт понял, кто общается с ним через бота-помощника, и начал делиться 
виртуальными номерами, укажи свой API-ключ, который ты найдешь в личном 
кабинете после регистрации на сайте\n\n
/send_api_key - отправить свой API-ключ\n
'''

SET_STATUS_RESPONSES = {'ACCESS_READY': 'Готовность номера подтверждена',
                        'ACCESS_RETRY_GET': 'Ожидание нового смс',
                        'ACCESS_ACTIVATION': 'Сервис успешно активирован',
                        'ACCESS_CANCEL': 'Активация отменена'}

STATUSES_GET_NUMBER = {'NO_NUMBERS': 'Нет номеров',
                       'NO_BALANCE': 'Закончился баланс',
                       'BAD_ACTION': 'Некорректное действие',
                       'BAD_SERVICE': 'Некорректное наименование сервиса',
                       'BAD_KEY': 'Неверный API-ключ',
                       'ERROR_SQL': 'Ошибка SQL-сервера',
                       'WRONG_EXCEPTION_PHONE': 'Некорректные исключающие префиксы',
                       'NO_BALANCE_FORWARD': 'Недостаточно средств для покупки переадресации'}

# funcs


async def edit_timer_message(message: Message, timer: int):
    """Редактирует сообщение таймера"""
    for seconds_left in range(timer, 0, -1):
        minutes = seconds_left // 60
        seconds = seconds_left - minutes * 60
        seconds = '0' + str(seconds) if seconds < 10 else seconds
        await asyncio.sleep(1)
        await message.edit_text(f'Ожидание смс: {minutes}:{seconds}', reply_markup=STOP_TIMER)

        if seconds_left == 1:
            await message.delete()


async def delete_message(message: Message):
    await message.delete()


async def send_timer_message(user_id: Integer, timer_minutes: int):
    return await bot.send_message(user_id, f'Ожидание смс: {timer_minutes}:00')


async def send_status_message(user_id: Integer, status_response: str):
    """
    Функция отправляет статус активации
    :param user_id:
    :param status_response:
    :return:
    """
    try:
        status_message = SET_STATUS_RESPONSES[status_response]
    except KeyError as err:
        BOT_APP_LOG.error(f'{err}, пользователь: {user_id}')
        return
    else:
        await bot.send_message(user_id, status_message)
