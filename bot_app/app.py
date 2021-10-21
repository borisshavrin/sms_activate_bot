from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from sms_activate_bot.settings import API_TOKEN_BOT, REDIS_HOST, REDIS_PORT

storage = RedisStorage2(host=REDIS_HOST, port=REDIS_PORT)

bot = Bot(token=API_TOKEN_BOT)
dp = Dispatcher(bot, storage=storage)
