import asyncio

import requests
from aiogram.dispatcher.storage import FSMContextProxy
from aiogram.utils import emoji
from aiogram.types.base import Integer

from .messages import send_status_message
from bot_app.app import bot
from services.models import Services
from sms_activate_bot.settings import API_BASE_URL


async def change_and_send_activation_status(data: FSMContextProxy, user_id: Integer):
    """
    Изменение статуса активации и отправка его пользователю
    :param data: Хранилище состояний
    :param user_id: идентификатор пользователя телеграм
    :return:
    """
    query_params = {'api_key': data['api_key'],
                    'action': data['action'],
                    'status': data['status'],
                    'id': data['activation_id']}

    change_status = requests.get(API_BASE_URL, params=query_params)
    await asyncio.sleep(1)
    status_response = change_status.text
    await send_status_message(user_id, status_response)
    return status_response


def get_price(service_code: str, api_key):
    """
    Получить актуальные цены с сайта sms-activate
    :param service_code: код сервиса
    :param api_key: ключ доступа
    :return: price_retail - розничная цена
    """
    query_params = {
        'api_key': api_key,
        'action': 'getPrices',
        'service': service_code,
        'country': 0
    }
    res = requests.get(API_BASE_URL, params=query_params)
    data_json = res.json()
    price_info = data_json['0']
    price_wholesale = price_info[service_code]['cost']  # оптовая цена
    price_retail = price_wholesale * 1.5  # розничная цена
    return price_retail


async def send_message_about_changed_price(user_id, changed_price):
    """
    Функция отправки сообщения об изменении цены
    :param user_id: идентификатор пользователя телеграм
    :param changed_price: словарь цен
    :return:
    """
    await bot.send_message(user_id, 'Изменение цен:')
    for service_name, prices in changed_price.items():
        emoj = emoji.emojize(':small_red_triangle:')
        if prices["old_price"] > prices["new_price"]:
            emoj = emoji.emojize(':small_red_triangle_down:')
        await bot.send_message(user_id,
                               f'{service_name}: {prices["old_price"]}р. -> {prices["new_price"]}р. {emoj}')


async def update_service_price(user_id, api_key):
    """
    Функция обновления цены сервисов.
    :param user_id: идентификатор пользователя телеграм
    :param api_key: ключ доступа
    :return:
    """
    services_code_list = await Services.get_code_list()
    changed_price = dict()
    for code_service in services_code_list:
        new_price = get_price(code_service, api_key)
        service = await Services.get_service_by_code(code_service)
        price = service.price
        service_name = service.name
        if price != new_price:
            await service.update_price(new_price)
            changed_price[service_name] = {'old_price': price, 'new_price': new_price}

    if changed_price:
        await send_message_about_changed_price(user_id, changed_price)
        # удаление словаря
        del changed_price
