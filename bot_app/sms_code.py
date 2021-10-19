import time

import requests
from asgiref.sync import sync_to_async


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
    """ Декоратор, повторяющий запрос 12раз (60сек) или пока не будет получен смс-код """
    def the_real_decorator(function):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < retry:
                try:
                    state = function(*args, **kwargs)
                    sms_code = state[1]
                except IndexError:
                    time.sleep(timeout)
                    retries += 1
                else:
                    return state
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
