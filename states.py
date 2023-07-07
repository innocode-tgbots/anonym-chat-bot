__all__ = ['OurStates']

from aiogram.dispatcher.filters.state import State, StatesGroup


class OurStates(StatesGroup):
    enter_name = State()
    yes_or_no = State()
    wait_for_partner = State()
    messaging = State()
