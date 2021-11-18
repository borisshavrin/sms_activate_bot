<h1 align="center">sms_activate_bot</h1>

<p align="center">
  <img src="https://img.shields.io/badge/made%20by-borisshavrin-brightgreen.svg" >
  <img src="https://img.shields.io/github/languages/top/borisshavrin/sms_activate_bot.svg">
  <img alt="GitHub code size in bytes" src="https://img.shields.io/github/languages/code-size/borisshavrin/sms_activate_bot">
  <img src="https://img.shields.io/badge/PRs-friendly-orange.svg?style=flat">
  <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/borisshavrin/sms_activate_bot?color=purple">
  <img alt="GitHub closed pull requests" src="https://img.shields.io/github/issues-pr-closed/borisshavrin/sms_activate_bot">
</p>


### Описание 

Привет! Данный телеграм-бот был создан для упрощенного получения виртуальных номеров, которые можно регистрировать в
определенных сервисах, например, в приложениях по доставке продуктов.  
  Для этого он использует API сайта [sms-activate.ru][1]


### Демо 

<p align="center">
  <img src="https://github.com/borisshavrin/sms_activate_bot/blob/master/static/github/img/titleBot.jpg" width=250px>
  <img src="https://github.com/borisshavrin/sms_activate_bot/blob/master/static/github/img/getNumber.GIF" width=250px>
  <img src="https://github.com/borisshavrin/sms_activate_bot/blob/master/static/github/img/getSms.GIF" width=250px>
</p>
  
  
### Технологии в проекте
- Python 3.8 + Django 3 + [Aiogram][2]
- SQLite/PostgreSQL
- [cryptography][3]
- Redis
- [asyncio][4]
  
Бот написан на Python 3.8 + Django 3 + [Aiogram][2], имеет ORM (БД: SQLite с возможностью перехода на PostgreSQL). Пароли (API-keys) пользователей хранятся в БД в зашифрованном с помощью библиотеки [cryptography][3] виде. Для хранения временных данных (например, параметры API-запросов) используется БД Redis, получающая эти данные в роли [Хранилища состояний][5] (State). Для создания фоновых задач помогает библиотека [asyncio][4].

  
### что-то характерное для проекта 
(проблемы, с которыми пришлось столкнуться, уникальные составляющие проекта);

  
Техническое описание проекта
-----
  
#### 1. Настройка и запуск бота

  > Иницаилизация в [bot/app.py][9]:
```python
from aiogram import Bot, Dispatcher

bot = Bot(token='your_token')
dp = Dispatcher(bot, storage='your_storage')
```

> Запуск в терминале: python [main.py][6]
```python
from aiogram import executor

from bot_app import dp

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
```


#### 2. Работа с командами и кнопками в [commands.py][8]
  
  > Отлавливаем сообщение (например, команду /send_api_key) с помощью декоратора .message_handler:
  
  ```python
  @dp.message_handler(commands=['send_api_key'], state='*')
  async def send_api_key(message: types.Message):
    ...
    await message.answer('Для добавления ключа, отправь его следующим сообщением')
  ```  
  > Отлавливаем callback (нажатие на кнопку) с помощью декоратора .callback_query_handler.  
  В качестве аргументов указываем **список кнопок** (а именно их callback_name`s), при нажатии на которые вызывается данная функция, и **состояние**, для которого данная функция должна отработать:
  ```python
  @dp.callback_query_handler(lambda c: c.data in SERVICES_CALLBACK_NAME_LIST, state=States.get_service)
  async def get_number_for_chosen_service(callback_query: types.CallbackQuery, state: FSMContext):
    """Ф-ия срабатывает при выборе сервиса, нажатием на кнопку"""
    await bot.answer_callback_query(callback_query.id)
    callback_name = callback_query.data
    ...
  ```
    
  
  #### 3. Создание и установка состояний, позволяющих определить, когда и какие функции должны отработать
  > Создаем состояния в [states.py][7]:  
  ```python
  from aiogram.dispatcher.filters.state import State, StatesGroup


  class States(StatesGroup):
    start = State()
    get_service = State()
    get_api_key = State()
    api_key_ready = State()
  ```  
  > Устанавливаем состояние в [commands.py][8]:
  ```python
  @dp.message_handler(commands=['send_api_key'], state='*')
  async def send_api_key(message: types.Message):
    await States.get_api_key.set()                          # установка состояния
    await message.answer('Для добавления ключа, отправь его следующим сообщением')
  ```  
  
#### 4. Шифрование API-key  
> Единоразово создаем ключ шифрования, вызывая из файла [crypto.py][3] слудующую функцию:
```python
  from cryptography.fernet import Fernet

  from sms_activate_bot.settings import BASE_DIR


  def write_key():
    key = Fernet.generate_key()
    with open(f'{BASE_DIR}/crypto/crypto.key', 'wb') as key_file:
        key_file.write(key)
```
> Обращение к созданному ключу:
```python
  def load_key():
    return open(f'{BASE_DIR}/crypto/crypto.key', 'rb').read()
```
> Пример шифрования предоставлен ниже. Однотипным способом реализован и механизм расшифровки.
```python
  def encrypt(text):
    key = load_key()
    cipher = Fernet(key)
    encrypted_text = cipher.encrypt(text)
    return encrypted_text
```
> Шифрование в уже знакомой функции отлова ключа, отправленного боту следующим сообщением:
```python
  @dp.message_handler(content_types=["text"], state=States.get_api_key)
  async def get_api_key(message: types.Message):
    text_b = message.text.encode('utf-8')
    api_key = crypto.encrypt(text_b)
    ...
```
> Расшифровка ключа:
```python
  @dp.message_handler(commands=['get_sim'], state='*')
  async def get_sim(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await Users.get_user(user_id)
    text_b = crypto.decrypt(user.api_key)
    api_key = text_b.decode('utf-8')
    ...
```  
  
#### 5. Использование Хранилища состояний
  
> Запись данных:
```python
  @dp.callback_query_handler(lambda c: c.data in SERVICES_CALLBACK_NAME_LIST, state=States.get_service)
  async def get_number_for_chosen_service(callback_query: types.CallbackQuery, state: FSMContext):
    ...
    service = await Services.get_service_by_callback(callback_name)
    async with state.proxy() as data:
        data['service'] = service.code
    ...
```
> Получение данных:
```python
    url = data['api_base_url']
    query_params = {'api_key': data['api_key'],   # ключ также был записан, чтобы не обращаться каждый раз к основной БД
                    'action': data['action'],
                    'service': data['service'],
                    'country': data['country']}
    ...
```
  
#### 6. Использование клавиатур [keyboards.py][10]
```python
  from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
  import emoji
  ...
```
> emoji:
```python
  ready_emoji = emoji.emojize(':check_mark_button:')
  cancel_emoji = emoji.emojize(':cross_mark:')
```
> Создание кнопок:
```python
  inline_btn_access_ready = InlineKeyboardButton(ready_emoji, callback_data='1')
  inline_btn_access_cancel = InlineKeyboardButton(cancel_emoji, callback_data='8')
```
> Создание клавиатуры и добавление к ней кнопок:
```python
  ACCESS = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
  ACCESS.add(inline_btn_access_ready, inline_btn_access_cancel)
```
> Создание клавиатуры сервисов с помощью функции:
```python
  from asgiref.sync import sync_to_async
  ...
  @sync_to_async
  def get_service_keyboard(callback=None, current_page=1):
    """Первоначальный вывод кнопок с сервисами и работающими callback или/
    Редактирование нажатой кнопки и назначение нераработающих callback"""

    service_keyboard_list = []
    for service in SERVICES_QUERYSET:
        text = f'{service.name}: {service.price}р.'
        if callback is None:
            callback_data = service.callback_name
        else:
            callback_data = 'none_callback'
            if service.callback_name == callback:
                text = f'{service.name}: {service.price}р.   {choice_emoji}'

        inline_btn_service = [InlineKeyboardButton(text, callback_data=callback_data)]    # создание кнопок сервисов
        service_keyboard_list.append(inline_btn_service)                                  # добавление в список для пагинации
    ...
```
#### 7. Пагинация
> Создаем кнопки перемещения:
```python
pre_paginator_btn = InlineKeyboardButton('<-', callback_data='<-')
next_paginator_btn = InlineKeyboardButton('->', callback_data='->')
```
> Создаем объект для пагинации, в качестве аргументов передаем сформированный список кнопок сервисов и количество выводимых сервисов на одной странице:
```python
  from django.core.paginator import Paginator
  ...
  @sync_to_async
  def get_service_keyboard(callback=None, current_page=1):
    ...
    p = Paginator(service_keyboard_list, 5)
    ...
```
> Добавляем условия для callback кнопок перемещения, чтобы исключить нажатие при достижении правой/левой границ:
```python
    if current_page == 1:
        pre_paginator_btn.callback_data = 'none_callback'
    if current_page > 1:
        pre_paginator_btn.callback_data = '<-'
    if current_page == p.num_pages:
        next_paginator_btn.callback_data = 'none_callback'
    if current_page < p.num_pages:
        next_paginator_btn.callback_data = '->'
    if callback is not None:
        pre_paginator_btn.callback_data = 'none_callback'
        next_paginator_btn.callback_data = 'none_callback'
```
> Создаем неактивную кнопку текущей страницы и добавляем все созданные кнопки в общую клавиатуру (текущую страницу с 5-ю сервисами и в конец кнопки перемещения):
```python
    current_page_btn = InlineKeyboardButton(text=f'{current_page}', callback_data='none_callback')
    service_keyboard = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=p.page(current_page)).row(
        pre_paginator_btn, current_page_btn, next_paginator_btn
    )
    return service_keyboard
```

#### 8. Выполнение запросов
> Выполняем запрос, используя данные из Хранилища состояний как параметры запроса:
```python
query_params = {'api_key': data['api_key'],
                'action': data['action'],
                'service': data['service'],
                'country': data['country']}
res = requests.get(API_BASE_URL, params=query_params)
result = res.text.split(':')
status = result[0]
...
```
> Получаем номер:
```python
try:
    activation_id = result[1]
    phone = result[2][1:]
...
```

#### 9. Использование фоновых задач (Tasks)
> Создание задачи (аргументами являются функция, которую необходимо выполнить, и имя задачи):
```python
asyncio.create_task(
    start_timer_and_get_sms_code(user_id=user_id, state=state),
    name=f'sms-{user_id}'
)
...
```
> Поиск задачи среди всех запущенных задач:
```python
tasks = asyncio.all_tasks()
task_timer, task_sms = None, None
for task in tasks:
    if task.get_name() == f'sms-{user_id}':
        task_sms = task
    if task.get_name() == f'timer-{user_id}':
        task_timer = task
...
```
> Каждую отловленную задачу при необходимости можно отменить:
```python
task_timer.cancel()
...
task_sms.cancel()
```
  
[1]: https://sms-activate.ru/ru/api2
[2]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/app.py#:~:text=storage%20%3D%20RedisStorage2(host,bot%2C%20storage%3Dstorage)
[3]: https://github.com/borisshavrin/sms_activate_bot/blob/master/crypto/crypto.py
[4]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/commands.py#:~:text=data%5B%27page%27%5D%20%3D%201-,await%20asyncio.sleep(1),asyncio.create_task(update_service_price(user_id%2C%20api_key)),-service_keyboard%20%3D%20await%20get_service_keyboard
[5]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/commands.py#:~:text=await%20States.get_service,data%5B%27page%27%5D%20%3D%201
[6]: https://github.com/borisshavrin/sms_activate_bot/blob/master/main.py
[7]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/states.py
[8]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/commands.py
[9]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/app.py
[10]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/keyboards.py
