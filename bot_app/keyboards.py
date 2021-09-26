from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.models import Services


inline_btn_help = InlineKeyboardButton('/help', callback_data='help')
HELP = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(inline_btn_help)

SERVICES = InlineKeyboardMarkup(resize_keyboard=True)
services_all = Services.objects.all()
for service in services_all:
    inline_btn_service = InlineKeyboardButton(f'{service.name}, цена: {service.price}',
                                              callback_data=service.callback_name)
    SERVICES.add(inline_btn_service)
