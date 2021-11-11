<h1 align="center">sms_activate_bot</h1>

<p align="center">
  <img src="https://img.shields.io/badge/made%20by-borisshavrin-brightgreen.svg" >
  <img src="https://img.shields.io/github/languages/top/borisshavrin/sms_activate_bot.svg">
  <img alt="GitHub code size in bytes" src="https://img.shields.io/github/languages/code-size/borisshavrin/sms_activate_bot">
  <img src="https://img.shields.io/badge/PRs-friendly-orange.svg?style=flat">
  <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/borisshavrin/sms_activate_bot?color=purple">
  <img alt="GitHub closed pull requests" src="https://img.shields.io/github/issues-pr-closed/borisshavrin/sms_activate_bot">
</p>


<p align="center">
  <img src="https://github.com/borisshavrin/sms_activate_bot/blob/master/static/github/img/bot_info.png"
</p>

### Описание 

Привет! Данный телеграм-бот был создан для упрощенного получения виртуальных номеров, которые можно регистрировать в
определенных сервисах, например, в приложениях по доставке продуктов.  
  Для этого он использует API сайта [sms-activate.ru][1]


### Демо 

(изображения, ссылки на видео, интерактивные демо-ссылки);
  
  
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
(установка, настройка, как помочь проекту).
  
  
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
  ...
  def load_key():
    return open(f'{BASE_DIR}/crypto/crypto.key', 'rb').read()
```
> Пример шифрования предоставлен ниже. Однотипным способом реализован и механизм расшифровки
```python
  ...
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
> Расшифровка и помещение ключа в Хранилище состояний для дальнейшего использования уже без обращения к основной БД:
```python
  @dp.message_handler(commands=['get_sim'], state='*')
  async def get_sim(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await Users.get_user(user_id)
    text_b = crypto.decrypt(user.api_key)
    api_key = text_b.decode('utf-8')
    await States.get_service.set()
    async with state.proxy() as data:
        """ Добавление данных в Хранилище состояний (Redis) """
        ...
        data['api_key'] = api_key
        ...
```

  
[1]: https://sms-activate.ru/ru/api2
[2]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/app.py#:~:text=storage%20%3D%20RedisStorage2(host,bot%2C%20storage%3Dstorage)
[3]: https://github.com/borisshavrin/sms_activate_bot/blob/59f819609db73bbb362752e29224a4030e8e661e/crypto/crypto.py
[4]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/commands.py#:~:text=data%5B%27page%27%5D%20%3D%201-,await%20asyncio.sleep(1),asyncio.create_task(update_service_price(user_id%2C%20api_key)),-service_keyboard%20%3D%20await%20get_service_keyboard
[5]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/commands.py#:~:text=await%20States.get_service,data%5B%27page%27%5D%20%3D%201
[6]: https://github.com/borisshavrin/sms_activate_bot/blob/48a4d107475ad997b2e9e028cf8ee9dff6a2673c/main.py
[7]: https://github.com/borisshavrin/sms_activate_bot/blob/bd0828f2c2bfe8792bd5ff0958df8dc81a1b6670/bot_app/states.py
[8]: https://github.com/borisshavrin/sms_activate_bot/blob/48a4d107475ad997b2e9e028cf8ee9dff6a2673c/bot_app/commands.py
[9]: https://github.com/borisshavrin/sms_activate_bot/blob/bd0828f2c2bfe8792bd5ff0958df8dc81a1b6670/bot_app/app.py
