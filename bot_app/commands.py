from aiogram import types
from aiogram.dispatcher import FSMContext
import time
import requests

from sms_activate_bot.settings import API_TOKEN_SMS_ACTIVATE
from .app import dp, bot

from .messages import WELCOME_MESSAGE
from .keyboards import SERVICES, HELP
from .states import States

COMMANDS = '/help \n/balance \n/get_sim \n/lastsms'


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    time.sleep(1)
    await message.answer(WELCOME_MESSAGE, reply_markup=HELP)


@dp.message_handler(commands=['help'])
async def start_message(message: types.Message):
    time.sleep(1)
    await message.reply('Список доступных комманд:')
    await message.answer(f'{COMMANDS}')


@dp.message_handler(commands=['send_api_key'], state='*')
async def send_api_key(message: types.Message, state: FSMContext):
    await States.get_api_key.set()          # установка состояния
    await message.answer('Для добавления ключа, отправь его следующим сообщением')


@dp.message_handler(content_types=["text"], state=States.get_api_key)
async def get_api_key(message: types.Message, state: FSMContext):
    api_key = message.text



@dp.message_handler(commands=['balance'])
async def get_balance(message: types.Message):
    res = requests.get(f'https://sms-activate.ru/stubs/handler_api.php?'
                       f'api_key=${API_TOKEN_SMS_ACTIVATE}&action=getBalance')
    balance = res.text.split(':')[1]
    time.sleep(1)
    await message.answer(f'Баланс: {balance}')


@dp.message_handler(commands=['get_sim'], state='*')
async def get_sim(message: types.Message, state: FSMContext):
    await States.get_service.set()
    async with state.proxy() as data:               # добавление данных в Хранилище состояний (MemoryStorage)
        data['api_base_url'] = 'https://sms-activate.ru/stubs/handler_api.php?'
        data['api_key'] = f'${API_TOKEN_SMS_ACTIVATE}'
        data['action'] = 'getNumber'
    time.sleep(1)
    await message.answer('Выберите сервис:', reply_markup=SERVICES)


@dp.callback_query_handler(lambda c: c.data in ['5ka', 'samokat', 'bk', 'ozon', 'dc', 'all'],
                           state=States.get_service)
async def get_service(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    answer = callback_query.data                            # ответ пользователя
    time.sleep(1)
    async with state.proxy() as data:
        await bot.send_message(callback_query.from_user.id,
                               f'Вы выбрали {answer} and {data}', reply_markup=SERVICES)
