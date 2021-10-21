from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import emoji
from asgiref.sync import sync_to_async

from services.models import Services

# emoji

choice_emoji = emoji.emojize('👈🏻')
ready_emoji = emoji.emojize('✅')
cancel_emoji = emoji.emojize('❌')
stop_timer_emoji = emoji.emojize('🙅‍♂️')
SERVICES_QUERYSET = Services.objects.all()

# keyboards

ACCESS = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
inline_btn_access_ready = InlineKeyboardButton(ready_emoji, callback_data='1')
inline_btn_access_cancel = InlineKeyboardButton(cancel_emoji, callback_data='8')
ACCESS.add(inline_btn_access_ready, inline_btn_access_cancel)

STOP_TIMER = InlineKeyboardMarkup(one_time_keyboard=True)
inline_btn_stop_timer = InlineKeyboardButton(stop_timer_emoji, callback_data='stop')
STOP_TIMER.add(inline_btn_stop_timer)


# funcs

@sync_to_async
def get_service_keyboard(callback=None):
    """Первоначальный вывод кнопок с сервисами и работающими callback или/
    Редактирование нажатой кнопки и назначение нераработающих callback"""
    service_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
    for service in SERVICES_QUERYSET:
        text = f'{service.name}: {service.price}р.'
        if callback is None:
            callback_data = service.callback_name
        else:
            callback_data = 'none_callback'
            if service.callback_name == callback:
                text = f'{service.name}: {service.price}р.   {choice_emoji}'

        inline_btn_service = InlineKeyboardButton(text, callback_data=callback_data)
        service_keyboard.add(inline_btn_service)
    return service_keyboard
