from aiogram import types
from aiogram.dispatcher import FSMContext
import requests
import asyncio

from django.core.exceptions import ObjectDoesNotExist

from services.models import Services
from users.models import Users

from .app import dp, bot
from .messages import WELCOME_MESSAGE, COMMANDS, edit_message, setStatus_responses
from .keyboards import SERVICES, ACCESS, ready_emoji
from .sms_code import get_sms_code
from .states import States


@dp.message_handler(commands=['start'], state='*')
async def start_message(message: types.Message):
    await asyncio.sleep(0.5)
    await message.answer(WELCOME_MESSAGE)


@dp.message_handler(commands=['help'], state='*')
async def help_message(message: types.Message):
    await asyncio.sleep(0.5)
    await message.reply('Список доступных комманд:')
    await message.answer(f'{COMMANDS}')


@dp.message_handler(commands=['send_api_key'], state='*')
async def send_api_key(message: types.Message, state: FSMContext):
    await States.get_api_key.set()          # установка состояния
    await message.answer('Для добавления ключа, отправь его следующим сообщением')


@dp.message_handler(content_types=["text"], state=States.get_api_key)
async def get_api_key(message: types.Message, state: FSMContext):
    api_key = message.text
    user_id = message.from_user.id
    try:
        user = await Users.get_user(user_id)
    except ObjectDoesNotExist:
        await Users.create_user(user_id, api_key)
        await message.answer('Пользователь создан!')
    else:
        user.update_api_key(api_key)
        await message.answer('Ключ обновлен!')
    finally:
        await asyncio.sleep(0.5)
        await States.api_key_ready.set()
        await message.answer('Теперь вам доступен заказ номеров, воспользуйтесь командой /get_sim')


@dp.message_handler(commands=['balance'], state='*')
async def get_balance(message: types.Message):
    user_id = message.from_user.id
    user = await Users.get_user(user_id)
    query_params = {'api_key': user.api_key,
                    'action': 'getBalance'}
    url = 'https://sms-activate.ru/stubs/handler_api.php'
    res = requests.get(url, params=query_params)
    balance = res.text.split(':')[1]
    await asyncio.sleep(1)
    await message.answer(f'Баланс: {balance}')


@dp.message_handler(commands=['get_sim'], state='*')
async def get_sim(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await Users.get_user(user_id)
    await States.get_service.set()
    async with state.proxy() as data:
        """ Добавление данных в Хранилище состояний (Redis) """
        data['api_base_url'] = 'https://sms-activate.ru/stubs/handler_api.php'
        data['api_key'] = user.api_key
        data['action'] = 'getNumber'
        data['country'] = '0'
    await asyncio.sleep(1)
    await message.answer('Выберите сервис:', reply_markup=SERVICES)


services_callback_name_list = Services.get_callback_name_list()


@dp.callback_query_handler(lambda c: c.data in services_callback_name_list, state=States.get_service)
async def get_service(callback_query: types.CallbackQuery, state: FSMContext):
    """Ф-ия срабатывает при выборе сервиса, нажатием на кнопку"""
    await bot.answer_callback_query(callback_query.id)
    callback_name = callback_query.data
    service = await Services.find_service(callback_name)
    async with state.proxy() as data:
        data['service'] = service.code

    url = data['api_base_url']
    query_params = {'api_key': data['api_key'],
                    'action': data['action'],
                    'service': data['service'],
                    'country': data['country']}
    res = requests.get(url, params=query_params)
    result = res.text.split(':')
    status = result[0]
    try:
        activation_id = result[1]
        phone = result[2][1:]
    except IndexError:
        message = 'Нет номеров' if status == "NO_NUMBERS" else 'Закончился баланс'
        await bot.send_message(callback_query.from_user.id, message)
    else:
        async with state.proxy() as data:
            data['activation_id'] = activation_id

        await bot.send_message(callback_query.from_user.id, f'Ваш номер для сервиса "{service.name}":\n{phone}')
        await bot.send_message(callback_query.from_user.id,
                               f'Нажмите {ready_emoji} после того как смс будет отправлено', reply_markup=ACCESS)


@dp.callback_query_handler(lambda c: c.data in ['1', '8'], state=States.get_service)
async def change_activation_status_and_get_sms(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    status = callback_query.data                # 1 or 8
    async with state.proxy() as data:
        data['action'] = 'setStatus'
        data['status'] = status

    status_response = await change_activation_status(data, user_id)

    if status_response == 'ACCESS_READY':
        timer_minutes = 5
        timer_message = await bot.send_message(user_id, f'Ожидание смс: {timer_minutes}:00')
        task_edit_message = asyncio.create_task(edit_message(message=timer_message, timer=timer_minutes * 60 - 1))

        try:
            sms = await get_sms_code(data)
            sms = sms[:]
        except TypeError:
            await bot.send_message(user_id, 'Смс не пришло')
            async with state.proxy() as data:
                data['status'] = '8'
        else:
            await bot.send_message(user_id, f'смс-код: {sms}')
            await timer_message.delete()
            async with state.proxy() as data:
                data['status'] = '6'
        finally:
            task_edit_message.cancel()
            await change_activation_status(data, user_id)


async def change_activation_status(data, user_id):
    url = data['api_base_url']
    query_params = {'api_key': data['api_key'],
                    'action': data['action'],
                    'status': data['status'],
                    'id': data['activation_id']}

    change_status = requests.get(url, params=query_params)
    await asyncio.sleep(1)
    status_response = change_status.text
    message = setStatus_responses[status_response]
    await bot.send_message(user_id, message)
    return status_response


@dp.callback_query_handler(lambda c: c.data in ['stop'], state=States.get_service)
async def stop_timer(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    message = callback_query.message
    async with state.proxy() as data:
        data['status'] = '8'

    await message.delete()
    await change_activation_status(data, user_id)
