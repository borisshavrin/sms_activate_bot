from aiogram import types
from aiogram.dispatcher import FSMContext
import requests
import asyncio

from django.core.exceptions import ObjectDoesNotExist

from services.models import Services
from users.models import Users

from .app import dp, bot
from .messages import WELCOME_MESSAGE, COMMANDS
from .keyboards import ACCESS, ready_emoji, get_service_keyboard
from .operations import change_and_send_activation_status
from .sms_code import start_timer_and_get_sms_code, TASKS
from .states import States

SERVICES_CALLBACK_NAME_LIST = Services.get_callback_name_list()


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
        data['user_id'] = user_id
    await asyncio.sleep(1)
    service_keyboard = await get_service_keyboard()
    await message.answer('Выберите сервис:', reply_markup=service_keyboard)


@dp.callback_query_handler(lambda c: c.data in SERVICES_CALLBACK_NAME_LIST, state=States.get_service)
async def get_number_for_chosen_service(callback_query: types.CallbackQuery, state: FSMContext):
    """Ф-ия срабатывает при выборе сервиса, нажатием на кнопку"""
    await bot.answer_callback_query(callback_query.id)
    callback_name = callback_query.data

    change_service_keyboard = await get_service_keyboard(callback_name)
    await callback_query.message.edit_reply_markup(reply_markup=change_service_keyboard)

    service = await Services.get_service_by_callback(callback_name)
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
            data['phone'] = phone

        await bot.send_message(callback_query.from_user.id, f'Ваш номер для сервиса "{service.name}":\n{phone}')
        await bot.send_message(callback_query.from_user.id,
                               f'Нажмите {ready_emoji} после того как смс будет отправлено', reply_markup=ACCESS)


@dp.callback_query_handler(lambda c: c.data in ['1', '8'], state=States.get_service)
async def get_sms_code(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_reply_markup(reply_markup=None)
    user_id = callback_query.from_user.id
    message = callback_query.message
    status = callback_query.data                # 1 or 8
    async with state.proxy() as data:
        data['action'] = 'setStatus'
        data['status'] = status

    status_response = await change_and_send_activation_status(data, user_id)
    if status_response == 'ACCESS_READY':
        task_sms = asyncio.create_task(
            start_timer_and_get_sms_code(user_id=user_id, state=state),
            name='sms'
        )
        TASKS[f'{user_id}-{message.message_id}-sms'] = task_sms


@dp.callback_query_handler(lambda c: c.data in ['stop'], state=States.get_service)
async def stop_timer(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    message = callback_query.message

    task_timer = TASKS[f'{user_id}-{message.message_id}-timer']
    task_sms = TASKS[f'{user_id}-{message.message_id - 2}-sms']
    task_timer.cancel()

    async with state.proxy() as data:
        data['status'] = '8'
    await message.delete()
    await change_and_send_activation_status(data, user_id)
    task_sms.cancel()
