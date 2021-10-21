import asyncio
import time

import requests
from aiogram.dispatcher.storage import FSMContext, FSMContextProxy
from aiogram.types.base import Integer
from asgiref.sync import sync_to_async

from activations.models import Activations
from bot_app.app import bot
from bot_app.messages import edit_timer_message, send_timer_message
from bot_app.operations import change_and_send_activation_status
from services.models import Services
from users.models import Users


def sleep_state(timeout: int, retry=12 * 5):
    """ Декоратор, повторяющий запрос каждые 5 сек (5мин) или пока не будет получен смс-код """
    def the_real_decorator(function):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < retry:
                try:
                    state = function(*args, **kwargs)
                    sms_code = state[1]
                except IndexError:
                    time.sleep(timeout)
                    retries += 1
                else:
                    return state
        return wrapper
    return the_real_decorator


@sync_to_async
def get_sms_code(data: FSMContextProxy):
    action = 'getStatus'
    url = data['api_base_url']
    query_params = {
        'api_key': data['api_key'],
        'action': action,
        'id': data['activation_id']
    }
    activation_state = get_activation_state(url, query_params)
    try:
        sms_code = activation_state[1]
    except TypeError:
        return None
    else:
        return sms_code


@sleep_state(5)
def get_activation_state(url: str, query_params):
    try:
        get_state = requests.get(url, params=query_params)
        state = get_state.text.split(':')
    except requests.exceptions.Timeout as err:
        # Отправка admin / log
        print(f'The request timed out: {err.response} для {url}')
        # Повторное поднятие ошибки исключения для декоратора
        raise requests.exceptions.Timeout
    else:
        return state


async def start_timer_and_get_sms_code(user_id: Integer, state: FSMContext, timer_minutes=5):
    timer_message = await send_timer_message(user_id, timer_minutes)
    task_edit_message = asyncio.create_task(edit_timer_message(message=timer_message, timer=timer_minutes * 60 - 1))

    try:
        async with state.proxy() as data:
            sms = await get_sms_code(data)
            sms = sms[:]
    except TypeError:
        await bot.send_message(user_id, 'Смс не пришло')
        async with state.proxy() as data:
            data['status'] = '8'
    else:
        await bot.send_message(user_id, f'Ваш код: {int(sms)}')
        await timer_message.delete()
        async with state.proxy() as data:
            data['status'] = '6'
            """Внесение активации в БД"""
            user = await Users.get_user(user_id=user_id)
            service = await Services.get_service_by_code(code=data['service'])
            await Activations.create_activation(
                id_activation=data['activation_id'],
                user=user,
                service=service,
                number=int(data['phone']),
                sms=int(sms)
            )
    finally:
        task_edit_message.cancel()
        await change_and_send_activation_status(data, user_id)
