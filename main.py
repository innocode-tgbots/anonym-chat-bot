import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text

from config import TOKEN
from states import OurStates  # noqa
from user_class import User

logging.basicConfig(level=logging.INFO)

user_mapping = dict()
user_mapping: dict[int, User]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())


@dp.message_handler(commands=['start'], state="*")
async def start_handler(message: types.Message):
    # user_id = message.from_user.id
    user_id = message.from_id

    if user_id not in user_mapping:
        user_mapping[user_id] = User(
            user_id=user_id
        )

    await message.answer(
        text='Привет! Я бот для знакомств. Напиши мне своё имя, чтобы найти себе пару!'
    )

    await OurStates.enter_name.set()


@dp.message_handler(state=OurStates.enter_name)
async def enter_name_handler(message: types.Message):
    user_id = message.from_id
    user_mapping[user_id].name = message.text
    text = f"Отлично, {user_mapping[user_id].name}! Сейчас я попробую найти тебе пару. "
    await message.answer(text=text)
    await message.answer(text="Ты готов? Напиши 'да', если да, и 'нет', если нет.")
    await OurStates.yes_or_no.set()


@dp.message_handler(
    Text(equals=('да', 'yes'), ignore_case=True),
    state=OurStates.yes_or_no)
async def wait_for_partner_handler(message: types.Message):
    # await OurStates.wait_for_partner.set()
    user = user_mapping[message.from_id]

    chosen = None

    for partner_id, partner_obj in user_mapping.items():
        if partner_id != user.user_id and partner_obj.partner_id is None:
            chosen = partner_id

    if chosen is not None:
        user.partner_id = chosen
        user_mapping[chosen].partner_id = user.user_id
        await message.answer(
            text=f"Ты сейчас связан с {user_mapping[chosen].name}! Напиши что-нибудь."
        )
        await dp.bot.send_message(
            chat_id=chosen,
            text=f"Ты сейчас связан с {user.name}! Напиши что-нибудь."
        )
        await OurStates.messaging.set()
    else:
        await message.answer(
            text="Пока никого нет, кто был бы свободен. Подожди немного."
        )


if __name__ == '__main__':
    executor.start_polling(
        dispatcher=dp,
        skip_updates=True
    )
