import asyncio

from aiogram.types import Message
from aiogram.types.base import Integer

from bot_app.app import bot
from bot_app.keyboards import STOP_TIMER

# text templates

COMMANDS = '/help \n/balance \n/get_sim'

WELCOME_MESSAGE = '''
Привет, это бот, который поможет тебе получить виртуальный номер.\n
Для начала работы, укажи свой API-ключ\n\n
/send_api_key - отправить свой API-ключ\n
/help - для получения списка команд\n'''

SET_STATUS_RESPONSES = {'ACCESS_READY': 'готовность номера подтверждена',
                        'ACCESS_RETRY_GET': 'ожидание нового смс',
                        'ACCESS_ACTIVATION': 'сервис успешно активирован',
                        'ACCESS_CANCEL': 'активация отменена'}


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
    status_message = SET_STATUS_RESPONSES[status_response]
    await bot.send_message(user_id, status_message)
