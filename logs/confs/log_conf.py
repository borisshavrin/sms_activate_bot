import logging
import os.path
from logging.handlers import TimedRotatingFileHandler

PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs'))
FILE_NAME = os.path.join(PATH, 'bot_app.log')

BOT_APP_LOG = logging.getLogger('bot_app_log')
BOT_APP_LOG.setLevel(logging.INFO)

FILE_HANDLER = TimedRotatingFileHandler(FILE_NAME, encoding='utf-8', interval=1, when='D')
FILE_HANDLER.setLevel(logging.DEBUG)

FORMATTER = logging.Formatter('%(asctime)-29s %(levelname)-10s %(module)-23s %(message)s')
FILE_HANDLER.setFormatter(FORMATTER)

BOT_APP_LOG.addHandler(FILE_HANDLER)

if __name__ == '__main__':
    BOT_APP_LOG.critical('Критическая ошибка')
    BOT_APP_LOG.error('Ошибка')
    BOT_APP_LOG.warning('Внимание')
    BOT_APP_LOG.debug('Отладочная информация')
    BOT_APP_LOG.info('информационное сообщение')
