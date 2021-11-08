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
<p>Для этого он использует API сайта https://sms-activate.ru/ru/api2.</p>


### Демо 

(изображения, ссылки на видео, интерактивные демо-ссылки);
### Технологии в проекте
Бот написан на Python v3.8 + Django v3.2.7 + Aiogram, имеет ORM (БД: SQLite с возможностью перехода на PostgreSQL). Пароли (API-keys) пользователей хранятся в БД в зашифрованном с помощью библиотеки cryptography виде. Для хранения временных данных (например, параметры API-запросов) используется БД Redis, получающая эти данные в роли Хранилища состояний (State). Для выполнения некоторых задач в фоне помогает библиотека asyncio

### что-то характерное для проекта 
(проблемы, с которыми пришлось столкнуться, уникальные составляющие проекта);
### Техническое описание проекта 
(установка, настройка, как помочь проекту).
