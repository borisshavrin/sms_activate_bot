from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from sms_activate_bot.settings import API_TOKEN_BOT

bot = Bot(token=API_TOKEN_BOT)
dp = Dispatcher(bot, storage=MemoryStorage())
