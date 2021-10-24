import asyncio

import requests
from aiogram.dispatcher.storage import FSMContextProxy

from aiogram.types.base import Integer

from .messages import send_status_message


async def change_and_send_activation_status(data: FSMContextProxy, user_id: Integer):
    url = data['api_base_url']
    query_params = {'api_key': data['api_key'],
                    'action': data['action'],
                    'status': data['status'],
                    'id': data['activation_id']}

    change_status = requests.get(url, params=query_params)
    await asyncio.sleep(1)
    status_response = change_status.text
    await send_status_message(user_id, status_response)
    return status_response
