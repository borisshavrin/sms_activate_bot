import asyncio

from bot_app.funcs import edit_message
from sms_activate_bot.celery import app


# @app.task
# @periodic_task(run_every=crontab(minute=0, hour='6,18'))
# def update_price(message):
#     user = await get_user(message.from_user.id)
#     query_params = {'api_key': user.api_key,
#                     'action': 'getPrices',
#                     'country': 0}
#     url = 'https://sms-activate.ru/stubs/handler_api.php'
#     res = requests.get(url, params=query_params)
#     services_json = res.json()['0']
#     data = {service: services_json[service]['cost'] for service in services_json}
#
#     time.sleep(1)
#     await message.answer(f'Актуальные цены:')
