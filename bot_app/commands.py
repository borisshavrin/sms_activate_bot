from aiogram import types
from aiogram.dispatcher import FSMContext
import time
import requests
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
import  asyncio
from services.models import Services
from users.models import Users
from .app import dp, bot

from .messages import WELCOME_MESSAGE
from .keyboards import SERVICES, HELP, ACCESS, ready_emoji
from .states import States
from .tasks import timer_message_task

COMMANDS = '/help \n/balance \n/get_sim \n/lastsms'


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    time.sleep(0.5)
    await message.answer(WELCOME_MESSAGE, reply_markup=HELP)
    timer_seconds = 60
    timer_message = await bot.send_message(message.from_user.id, f'Ожидание смс: {timer_seconds} сек')
    id_message = timer_message.message_id
    id_chat = timer_message.chat.id

    asyncio.run(timer_message_task(id_message, id_chat))


@dp.message_handler(commands=['help'])
async def help_message(message: types.Message):
    time.sleep(0.5)
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
    except ObjectDoesNotExist:
        await create_user(message.from_user.id, api_key)
        await message.answer('Пользователь создан!')
    finally:
        time.sleep(0.5)
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
    query_params = {'api_key': user.api_key,
                    'action': 'getBalance'}
    url = 'https://sms-activate.ru/stubs/handler_api.php'
    res = requests.get(url, params=query_params)
    balance = res.text.split(':')[1]
    time.sleep(1)
    await message.answer(f'Баланс: {balance}')


@dp.message_handler(commands=['get_sim'], state='*')
async def get_sim(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await States.get_service.set()
    async with state.proxy() as data:               # добавление данных в Хранилище состояний (MemoryStorage)
        data['api_base_url'] = 'https://sms-activate.ru/stubs/handler_api.php'
        data['api_key'] = user.api_key
        data['action'] = 'getNumber'
        data['country'] = '0'
    time.sleep(1)
    await message.answer('Выберите сервис:', reply_markup=SERVICES)


@sync_to_async
def find_service(callback_name):
    service = Services.objects.get(callback_name=callback_name)
    return service


services_queryset = Services.objects.all()
services_callback_name_list = [service.callback_name for service in services_queryset]


@dp.callback_query_handler(lambda c: c.data in services_callback_name_list, state=States.get_service)
async def get_service(callback_query: types.CallbackQuery, state: FSMContext):
    """Ф-ия срабатывает при выборе сервиса, нажатием на кнопку"""
    await bot.answer_callback_query(callback_query.id)
    service = await find_service(callback_query.data)
    async with state.proxy() as data:
        data['service'] = service.code

    url = data['api_base_url']
    query_params = {'api_key': data['api_key'],
                    'action': data['action'],
                    'service': data['service'],
                    'country': data['country']}
    res = requests.get(url, params=query_params)
    time.sleep(1)
    result = res.text.split(':')
    status = result[0]
    try:
        activation_id = result[1]
        async with state.proxy() as data:
            data['activation_id'] = activation_id
        phone = result[2][1:]
        await bot.send_message(callback_query.from_user.id, f'Ваш номер для сервиса "{service.name}":\n{phone}')
        await bot.send_message(callback_query.from_user.id,
                               f'Нажмите {ready_emoji} после того как смс будет отправлено', reply_markup=ACCESS)
    except IndexError:
        message = 'Нет номеров' if status == "NO_NUMBERS" else 'Закончился баланс'
        await bot.send_message(callback_query.from_user.id, message)


setStatus_responses = {'ACCESS_READY': 'готовность номера подтверждена',
                       'ACCESS_RETRY_GET': 'ожидание нового смс',
                       'ACCESS_ACTIVATION': 'сервис успешно активирован',
                       'ACCESS_CANCEL': 'активация отменена'}


@dp.callback_query_handler(lambda c: c.data in ['1', '8'], state=States.get_service)
async def change_activation_status_and_get_sms(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        status = callback_query.data
        data['action'] = 'setStatus'
        data['status'] = status

    url = data['api_base_url']
    query_params = {'api_key': data['api_key'],
                    'action': data['action'],
                    'status': data['status'],
                    'id': data['activation_id']}

    change_activation_status = requests.get(url, params=query_params)
    time.sleep(1)
    status_response = change_activation_status.text
    message = setStatus_responses[status_response]
    await bot.send_message(callback_query.from_user.id, message)
    if status_response == 'ACCESS_READY':
        timer_seconds = 60
        timer_message = await bot.send_message(callback_query.from_user.id, f'Ожидание смс: {timer_seconds} сек')
        id_message = timer_message.message_id
        id_chat = timer_message.chat.id
        timer_message_task.apply_async((id_message, id_chat))

    sms = await get_sms_code(data)
    await bot.send_message(callback_query.from_user.id, f'смс-код: {sms}')


@sync_to_async
def get_sms_code(data):
    action = 'getStatus'
    url = data['api_base_url']
    query_params = {
        'api_key': data['api_key'],
        'action': action,
        'id': data['activation_id']
    }
    activation_state = get_activation_state(url, query_params)
    sms_code = activation_state[1]
    return sms_code


def sleep_state(timeout, retry=12):
    def the_real_decorator(function):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < retry:
                try:
                    state = function(*args, **kwargs)
                    sms_code = state[1]
                    if sms_code:
                        return state
                except IndexError:
                    time.sleep(timeout)
                    retries += 1
        return wrapper
    return the_real_decorator


@sleep_state(5)
def get_activation_state(url, query_params):
    try:
        get_state = requests.get(url, params=query_params)
        state = get_state.text.split(':')
        return state
    except requests.exceptions.Timeout as err:
        # Отправка admin / log
        print(f'The request timed out: {err.response} для {url}')
        # Повторное поднятие ошибки исключения для декоратора
        raise requests.exceptions.Timeout
