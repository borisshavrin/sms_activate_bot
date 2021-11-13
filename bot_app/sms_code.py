import asyncio
import logging
import time
from asyncio import CancelledError

import requests
from aiogram.dispatcher.storage import FSMContext, FSMContextProxy
from aiogram.types.base import Integer
from asgiref.sync import sync_to_async
import logs.confs.log_conf

from activations.models import Activations
from bot_app.app import bot
from bot_app.messages import edit_timer_message, send_timer_message
from bot_app.operations import change_and_send_activation_status
from services.models import Services
from sms_activate_bot.settings import API_BASE_URL
from users.models import Users


BOT_APP_LOG = logging.getLogger('bot_app_log')


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
def get_sms_code(data: FSMContextProxy, task_edit_message):
    action = 'getStatus'
    query_params = {
        'api_key': data['api_key'],
        'action': action,
        'id': data['activation_id']
    }
    activation_state = get_activation_state(query_params, task_edit_message)
    try:
        sms_code = activation_state[1]
    except TypeError as err:
        BOT_APP_LOG.debug(err)
        return None
    else:
        return sms_code


@sleep_state(5)
def get_activation_state(query_params, task_edit_message):
    try:
        get_state = requests.get(API_BASE_URL, params=query_params)
        state = get_state.text.split(':')
    except requests.exceptions.Timeout as err:
        # Отправка admin / log
        BOT_APP_LOG.error(f'The request timed out: {err.response} для {API_BASE_URL}')
        # Повторное поднятие ошибки исключения для декоратора
        raise requests.exceptions.Timeout
    else:
        if task_edit_message.done():
            state.append('sms-code received!')                # Позволяет завершить цикл while досрочно
        return state


async def start_timer_and_get_sms_code(user_id: Integer, state: FSMContext, timer_minutes=5):
    timer_message = await send_timer_message(user_id, timer_minutes)
    task_edit_message = asyncio.create_task(
        edit_timer_message(message=timer_message, timer=timer_minutes * 60 - 1),
        name=f'timer-{user_id}-{timer_message.message_id}'
    )

    try:
        async with state.proxy() as data:
            sms = await get_sms_code(data, task_edit_message)
            sms = sms[:]
    except TypeError as err:
        BOT_APP_LOG.debug(f'Смс не пришло, error: {err}')
        await bot.send_message(user_id, 'Смс не пришло')
        async with state.proxy() as data:
            data['status'] = '8'

    except CancelledError:
        BOT_APP_LOG.error(f'Таск пользователя {user_id} был завершен')
        return

    else:
        service = await Services.get_service_by_code(data['service'])
        await bot.send_message(user_id, f'Ваш код для входа в {service.name}:\n{int(sms)}')
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
