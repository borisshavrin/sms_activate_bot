from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


inline_btn_help = InlineKeyboardButton('/help', callback_data='help')
HELP = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(inline_btn_help)

inline_btn_service_5ka = InlineKeyboardButton('5ka', callback_data='5ka')
inline_btn_service_samokat = InlineKeyboardButton('Самокат', callback_data='samokat')
inline_btn_service_bk = InlineKeyboardButton('Burger King', callback_data='bk')
inline_btn_service_ozon = InlineKeyboardButton('Ozon', callback_data='ozon')
inline_btn_service_dc = InlineKeyboardButton('Delivery Club', callback_data='dc')
inline_btn_service_all = InlineKeyboardButton('All', callback_data='all')
SERVICES = InlineKeyboardMarkup(resize_keyboard=True)
SERVICES.add(inline_btn_service_5ka)
SERVICES.add(inline_btn_service_samokat)
SERVICES.add(inline_btn_service_bk)
SERVICES.add(inline_btn_service_ozon)
SERVICES.add(inline_btn_service_dc)
SERVICES.add(inline_btn_service_all)
