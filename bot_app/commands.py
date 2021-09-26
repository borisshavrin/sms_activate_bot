from aiogram import types
from aiogram.dispatcher import FSMContext
import time
import requests
from asgiref.sync import sync_to_async

from services.models import Services
from users.models import Users
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
async def help_message(message: types.Message):
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
    try:
        user = await get_user(message.from_user.id)
        await update_api_key(user, api_key)
        await message.answer('Ключ обновлен!')
    except:
        await create_user(message.from_user.id, api_key)
        await message.answer('Пользователь создан!')
    finally:
        await States.api_key_ready.set()
        await message.answer('Теперь вам доступен заказ номеров, воспользуйтесь командой /get_sim')


@sync_to_async
def create_user(user_id, text):
    user = Users.objects.create(user_id_tg=user_id, api_key=text)
    user.save()


@sync_to_async
def update_api_key(user, api_key):
    user.api_key = api_key
    user.save()


@sync_to_async
def get_user(user_id):
    user = Users.objects.get(user_id_tg=user_id)
    return user


@dp.message_handler(commands=['balance'])
async def get_balance(message: types.Message):
    user = await get_user(message.from_user.id)
    res = requests.get(f'https://sms-activate.ru/stubs/handler_api.php?'
                       f'api_key=${user.api_key}&action=getBalance')
    balance = res.text.split(':')[1]
    time.sleep(1)
    await message.answer(f'Баланс: {balance}')


@dp.message_handler(commands=['get_sim'], state='*')
async def get_sim(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await States.get_service.set()
    async with state.proxy() as data:               # добавление данных в Хранилище состояний (MemoryStorage)
        data['api_base_url'] = 'https://sms-activate.ru/stubs/handler_api.php?'
        data['api_key'] = f'${user.api_key}'
        data['action'] = 'getNumber'
        data['country'] = '0'
    time.sleep(1)
    await message.answer('Выберите сервис:', reply_markup=SERVICES)


@sync_to_async
def find_service(callback_name):
    service = Services.objects.get(callback_name=callback_name)
    return service


@dp.callback_query_handler(lambda c: c.data in ['5ka', 'samokat', 'bk', 'ozon', 'dc', 'all'],
                           state=States.get_service)
async def get_service(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    service = await find_service(callback_query.data)
    time.sleep(1)
    async with state.proxy() as data:
        data['service'] = service.code

    res = requests.get(data['api_base_url'] + 'api_key=' + data['api_key'] + '&action=' + data['action'] +
                       '&service=' + data['service'] + '&country=' + data['country'])
    number = res.text.split(':')[2]
    await bot.send_message(
        callback_query.from_user.id, f'Ваш номер для сервиса "{service.name}":\n {number[1:]}')
