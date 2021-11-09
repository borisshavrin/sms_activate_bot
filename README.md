<h1 align="center">sms_activate_bot</h1>

<p align="center">
  <img src="https://img.shields.io/badge/made%20by-borisshavrin-brightgreen.svg" >
  <img src="https://img.shields.io/github/languages/top/borisshavrin/sms_activate_bot.svg">
  <img alt="GitHub code size in bytes" src="https://img.shields.io/github/languages/code-size/borisshavrin/sms_activate_bot">
  <img src="https://img.shields.io/badge/PRs-friendly-orange.svg?style=flat">
  <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/borisshavrin/sms_activate_bot?color=purple">
  <img alt="GitHub closed pull requests" src="https://img.shields.io/github/issues-pr-closed/borisshavrin/sms_activate_bot">
</p>

<h2 align="center">Bot info</h2>
<p align="center">
  <img src="https://github.com/borisshavrin/sms_activate_bot/blob/master/static/github/img/bot_info.png"
</p>

### Описание 

<p>Привет! Данный телеграм-бот был создан для упрощенного получения виртуальных номеров, которые можно регистрировать в
  определенных сервисах, например, в приложениях по доставке продуктов.</p>
<p>Для этого он использует API сайта [sms-activate.ru][1]


### Демо 

(изображения, ссылки на видео, интерактивные демо-ссылки);
### Технологии в проекте
Бот написан на Python 3.8 + Django 3 + [Aiogram][2]
имеет ORM (БД: SQLite с возможностью перехода на PostgreSQL). Пароли (API-keys) пользователей хранятся в БД в зашифрованном с помощью библиотеки [cryptography][3] виде. Для хранения временных данных (например, параметры API-запросов) используется БД Redis, получающая эти данные в роли [Хранилища состояний][5] (State). Для создания фоновых задач помогает библиотека [asyncio][4].

### что-то характерное для проекта 
(проблемы, с которыми пришлось столкнуться, уникальные составляющие проекта);

### Техническое описание проекта 
(установка, настройка, как помочь проекту).


[1]: https://sms-activate.ru/ru/api2
[2]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/app.py#:~:text=storage%20%3D%20RedisStorage2(host,bot%2C%20storage%3Dstorage)
[3]: https://github.com/borisshavrin/sms_activate_bot/blob/59f819609db73bbb362752e29224a4030e8e661e/crypto/crypto.py
[4]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/commands.py#:~:text=data%5B%27page%27%5D%20%3D%201-,await%20asyncio.sleep(1),asyncio.create_task(update_service_price(user_id%2C%20api_key)),-service_keyboard%20%3D%20await%20get_service_keyboard
[5]: https://github.com/borisshavrin/sms_activate_bot/blob/master/bot_app/commands.py#:~:text=await%20States.get_service,data%5B%27page%27%5D%20%3D%201
