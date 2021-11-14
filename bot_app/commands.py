import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
import requests
import asyncio

from django.core.exceptions import ObjectDoesNotExist
import logs.confs.log_conf

from crypto import crypto
from services.models import Services
from sms_activate_bot.settings import API_BASE_URL
from users.models import Users

from .app import dp, bot
from .messages import WELCOME_MESSAGE, COMMANDS, STATUSES_GET_NUMBER
from .keyboards import ACCESS, ready_emoji, get_service_keyboard
from .operations import change_and_send_activation_status, update_service_price
from .sms_code import start_timer_and_get_sms_code
from .states import States

SERVICES_CALLBACK_NAME_LIST = Services.get_callback_name_list()
BOT_APP_LOG = logging.getLogger('bot_app_log')


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
async def send_api_key(message: types.Message):
    await States.get_api_key.set()          # установка состояния
    await message.answer('Для добавления ключа, отправь его следующим сообщением')


@dp.message_handler(content_types=["text"], state=States.get_api_key)
async def get_api_key(message: types.Message):
    if message.text in COMMANDS:
        return await States.start.set()
    else:
        text_b = message.text.encode('utf-8')
        api_key = crypto.encrypt(text_b)
        user_id = message.from_user.id
        try:
            user = await Users.get_user(user_id)
        except ObjectDoesNotExist:
            BOT_APP_LOG.info(f'Создание пользователя {user_id}')
            await Users.create_user(user_id, api_key)
            await message.answer('Пользователь создан!')
        else:
            BOT_APP_LOG.info(f'Обновление API-key для пользователя {user_id}')
            await user.update_api_key(api_key)
            await message.answer('Ключ обновлен!')
        finally:
            await asyncio.sleep(0.5)
            await States.api_key_ready.set()
            await message.answer('Теперь вам доступен заказ номеров, воспользуйтесь командой /get_sim')


@dp.message_handler(commands=['balance'], state='*')
async def get_balance(message: types.Message):
    user_id = message.from_user.id
    user = await Users.get_user(user_id)
    text_b = crypto.decrypt(user.api_key)
    api_key = text_b.decode('utf-8')
    query_params = {'api_key': api_key,
                    'action': 'getBalance'}
    res = requests.get(API_BASE_URL, params=query_params)
    balance = res.text.split(':')[1]
    await asyncio.sleep(1)
    await message.answer(f'Баланс: {balance}')


@dp.message_handler(commands=['get_sim'], state='*')
async def get_sim(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await Users.get_user(user_id)
    text_b = crypto.decrypt(user.api_key)
    api_key = text_b.decode('utf-8')
    await States.get_service.set()
    async with state.proxy() as data:
        """ Добавление данных в Хранилище состояний (Redis) """
        data['api_key'] = api_key
        data['action'] = 'getNumber'
        data['country'] = '0'
        data['user_id'] = user_id
        data['page'] = 1
    await asyncio.sleep(1)
    asyncio.create_task(update_service_price(user_id, api_key))
    service_keyboard = await get_service_keyboard()
    await message.answer('Выберите сервис:', reply_markup=service_keyboard)


@dp.callback_query_handler(lambda c: c.data in SERVICES_CALLBACK_NAME_LIST, state=States.get_service)
async def get_number_for_chosen_service(callback_query: types.CallbackQuery, state: FSMContext):
    """Ф-ия срабатывает при выборе сервиса, нажатием на кнопку"""
    await bot.answer_callback_query(callback_query.id)
    callback_name = callback_query.data

    service = await Services.get_service_by_callback(callback_name)
    async with state.proxy() as data:
        data['service'] = service.code

    change_service_keyboard = await get_service_keyboard(callback_name, current_page=data['page'])
    await callback_query.message.edit_reply_markup(reply_markup=change_service_keyboard)

    query_params = {'api_key': data['api_key'],
                    'action': data['action'],
                    'service': data['service'],
                    'country': data['country']}
    res = requests.get(API_BASE_URL, params=query_params)
    result = res.text.split(':')
    status = result[0]
    try:
        activation_id = result[1]
        phone = result[2][1:]
    except IndexError as err:
        if status in STATUSES_GET_NUMBER.keys():
            message = STATUSES_GET_NUMBER[status]
            if status == 'BAD_KEY':
                message += '\nВоспользуйтесь командой /send_api_key'
        elif status.split(':')[0] == 'BANNED':
            message = status.split(':')[1] + '-время на которое аккаунт заблокирован'
        else:
            message = f'Повторите операцию позднее'
        await bot.send_message(callback_query.from_user.id, message)
        BOT_APP_LOG.error(f'error: {err} Статус получения номера для пользователя '
                          f'{callback_query.from_user.id}: {status}')
    else:
        async with state.proxy() as data:
            data['activation_id'] = activation_id
            data['phone'] = phone

        await bot.send_message(callback_query.from_user.id,
                               f'Ваш номер для сервиса "{service.name}":\n<code>{phone}</code>',
                               parse_mode='HTML')
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
        asyncio.create_task(
            start_timer_and_get_sms_code(user_id=user_id, state=state),
            name=f'sms-{user_id}'
        )
        await message.delete()


@dp.callback_query_handler(lambda c: c.data in ['stop'], state='*')
async def stop_timer(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    message = callback_query.message

    tasks = asyncio.all_tasks()
    task_timer, task_sms = None, None
    for task in tasks:
        if task.get_name() == f'sms-{user_id}':
            task_sms = task
        if task.get_name() == f'timer-{user_id}':
            task_timer = task
    task_timer.cancel()

    async with state.proxy() as data:
        data['status'] = '8'
    await message.delete()
    await change_and_send_activation_status(data, user_id)
    task_sms.cancel()


@dp.callback_query_handler(lambda c: c.data in ['<-', '->'], state=States.get_service)
async def paginator_services(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    callback_name = callback_query.data

    async with state.proxy() as data:
        if callback_name == '<-':
            data['page'] -= 1
        else:
            data['page'] += 1

    change_service_keyboard = await get_service_keyboard(current_page=data['page'])
    await callback_query.message.edit_reply_markup(reply_markup=change_service_keyboard)
