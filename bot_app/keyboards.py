from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import emoji

from services.models import Services


SERVICES = InlineKeyboardMarkup(resize_keyboard=True)
services_queryset = Services.objects.all()
for service in services_queryset:
    inline_btn_service = InlineKeyboardButton(f'{service.name}: {service.price}р.',
                                              callback_data=service.callback_name)
    SERVICES.add(inline_btn_service)

ACCESS = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
ready_emoji = emoji.emojize('✅')
cancel_emoji = emoji.emojize('❌')
inline_btn_access_ready = InlineKeyboardButton(ready_emoji, callback_data='1')
inline_btn_access_cancel = InlineKeyboardButton(cancel_emoji, callback_data='8')
ACCESS.add(inline_btn_access_ready, inline_btn_access_cancel)

STOP_TIMER = InlineKeyboardMarkup(one_time_keyboard=True)
stop_timer_emoji = emoji.emojize('🙅‍♂️')
inline_btn_stop_timer = InlineKeyboardButton(stop_timer_emoji, callback_data='stop')
STOP_TIMER.add(inline_btn_stop_timer)
