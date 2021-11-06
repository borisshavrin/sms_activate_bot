import requests
from aiogram.utils import emoji

from bot_app.app import bot
from services.models import Services


def get_price(service_code, api_key):
    url = 'https://sms-activate.ru/stubs/handler_api.php'
    query_params = {
        'api_key': api_key,
        'action': 'getPrices',
        'service': service_code,
        'country': 0
    }
    res = requests.get(url, params=query_params)
    data_json = res.json()
    price_info = data_json['0']
    price_wholesale = price_info[service_code]['cost']      # оптовая цена
    price_retail = price_wholesale * 1.5                    # розничная цена
    return price_retail


async def update_service_price(user_id, api_key):
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
        await bot.send_message(user_id, 'Изменение цен:')
        for service_name, prices in changed_price.items():
            emoj = emoji.emojize(':small_red_triangle:')
            if prices["old_price"] > prices["new_price"]:
                emoj = emoji.emojize(':small_red_triangle_down:')
            await bot.send_message(user_id,
                                   f'{service_name}: {prices["old_price"]}р. -> {prices["new_price"]}р. {emoj}')
