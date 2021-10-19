import asyncio

# text templates

COMMANDS = '/help \n/balance \n/get_sim'

WELCOME_MESSAGE = '''
Привет, это бот, который поможет тебе получить виртуальный номер.\n
Для начала работы, укажи свой API-ключ\n\n
/send_api_key - отправить свой API-ключ\n
/help - для получения списка команд\n'''

setStatus_responses = {'ACCESS_READY': 'готовность номера подтверждена',
                       'ACCESS_RETRY_GET': 'ожидание нового смс',
                       'ACCESS_ACTIVATION': 'сервис успешно активирован',
                       'ACCESS_CANCEL': 'активация отменена'}


# funcs

async def edit_message(message, timer):
    for seconds_left in range(timer, 0, -1):
        await asyncio.sleep(1)
        await message.edit_text(f'Ожидание смс: {seconds_left}')

        if seconds_left == 1:
            await message.delete()


async def delete_message(message):
    await message.delete()
