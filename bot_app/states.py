from aiogram.dispatcher.filters.state import State, StatesGroup


class States(StatesGroup):
    start = State()
    get_service = State()
    get_api_key = State()
    api_key_ready = State()
