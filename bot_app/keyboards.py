from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import emoji
from asgiref.sync import sync_to_async
from django.core.paginator import Paginator

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

pre_paginator_btn = InlineKeyboardButton('<-', callback_data='<-')
next_paginator_btn = InlineKeyboardButton('->', callback_data='->')
PAGINATOR_KB = InlineKeyboardMarkup(resize_keyboard=True)
PAGINATOR_KB.add(pre_paginator_btn, next_paginator_btn)


# funcs

@sync_to_async
def get_service_keyboard(callback=None, current_page=1):
    """Первоначальный вывод кнопок с сервисами и работающими callback или/
    Редактирование нажатой кнопки и назначение нераработающих callback"""

    service_keyboard_list = []
    for service in SERVICES_QUERYSET:
        text = f'{service.name}: {service.price}р.'
        if callback is None:
            callback_data = service.callback_name
        else:
            callback_data = 'none_callback'
            if service.callback_name == callback:
                text = f'{service.name}: {service.price}р.   {choice_emoji}'

        inline_btn_service = [InlineKeyboardButton(text, callback_data=callback_data)]
        service_keyboard_list.append(inline_btn_service)

    p = Paginator(service_keyboard_list, 5)

    if current_page == 1:
        pre_paginator_btn.callback_data = 'none_callback'
    if current_page > 1:
        pre_paginator_btn.callback_data = '<-'
    if current_page == p.num_pages:
        next_paginator_btn.callback_data = 'none_callback'
    if current_page < p.num_pages:
        next_paginator_btn.callback_data = '->'
    if callback is not None:
        pre_paginator_btn.callback_data = 'none_callback'
        next_paginator_btn.callback_data = 'none_callback'

    current_page_btn = InlineKeyboardButton(text=f'{current_page}', callback_data='none_callback')
    service_keyboard = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=p.page(current_page)).row(
        pre_paginator_btn, current_page_btn, next_paginator_btn
    )
    return service_keyboard
