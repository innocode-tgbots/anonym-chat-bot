import random

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from buttons import (
    greeting_kb,
    greeting_callback_data,
    skip_kb_menu,
    skip_callback_data, skip_kb_inline,
)
from config import TOKEN
from states import OurStates
from user_class import User

user_mapping = (
    dict()
)  # Создание словаря для отображения между идентификаторами пользователей и объектами пользователей
user_mapping: dict[int, User]  # Аннотация типа для словаря

bot = Bot(token=TOKEN)  # Создание объекта бота с использованием токена
dp = Dispatcher(
    bot=bot, storage=MemoryStorage()
)  # Создание диспетчера с использованием объекта бота и хранилища состояний в памяти


@dp.message_handler(
    commands=["start"], state="*"  # команда /start будет работать из любом состояния
)  # Обработчик команды /start для любого состояния
async def start_handler(message: types.Message):
    user_id = message.from_id

    if user_id not in user_mapping:  # Проверка, существует ли пользователь в словаре
        user_mapping[user_id] = User(
            user_id=user_id
        )  # Создание объекта User и добавление в словарь

    await message.reply(
        text="Привет! Я бот для знакомств. Напиши мне своё имя, чтобы найти себе пару!"
    )

    await OurStates.enter_name.set()  # Установка состояния enter_name


# dp.register_message_handler(start_handler, commands="start")


@dp.message_handler(
    state=OurStates.enter_name  # будет работать только в состоянии enter_name
)  # Обработчик для ввода имени пользователя
async def enter_name_handler(message: types.Message, state: FSMContext):
    user_id = message.from_id
    user = user_mapping[user_id]
    user.name = message.text  # Сохранение введенного имени пользователя

    text = f"Отлично, {user.name}! Сейчас я попробую найти тебе пару."
    await message.answer(text=text)

    to_user = await message.answer(text="Ты готов? Нажми на кнопку!", reply_markup=greeting_kb)
    await state.update_data(meet_with_message=to_user.message_id)
    await OurStates.yes_or_no.set()  # Установка состояния yes_or_no


async def get_random_partner(user_id: int) -> User:
    # Поиск свободного партнера среди пользователей в словаре
    shuffled_users = list(user_mapping.values())
    random.shuffle(shuffled_users)

    for partner_obj in shuffled_users:
        # Проверка, что пользователь не связан с самим собой
        # и что у партнера нет связи с другим пользователем
        if (
            # partner_id != user.user_id
            partner_obj.partner_id is None
            and partner_obj.name is not None
        ):
            # Получение текущего контекста партнера
            partner_context = dp.get_current().current_state(
                chat=partner_obj.id, user=partner_obj.id
            )
            # Где он находится на графе состояний
            partner_state = await partner_context.get_state()
            # Если он в состоянии "ожидает партнера", то выбираем его
            if partner_state == OurStates.wait_for_partner.state:
                return partner_obj


@dp.callback_query_handler(
    greeting_callback_data.filter(), state=OurStates.wait_for_partner
)
@dp.callback_query_handler(greeting_callback_data.filter(), state=OurStates.yes_or_no)
async def wait_for_partner_handler(
    call: types.CallbackQuery, state: FSMContext
):
    message = call.message  # Получение объекта сообщения под которым расположена кнопка
    user_id = call.from_user.id
    user = user_mapping[user_id]

    await bot.answer_callback_query(
        call.id
    )  # Ответ на нажатие кнопки, чтобы кнопка не подсвечивалась(была отжата)

    await message.reply(
        "Сейчас попробуем тебе найти партнёра...", reply_markup=skip_kb_menu
    )
    await OurStates.wait_for_partner.set()  # Установка состояния wait_for_partner

    partner = await get_random_partner(user_id)  # Переменная для хранения идентификатора партнера

    if partner is not None:
        partner_state = dp.get_current().current_state(chat=partner.id, user=partner.id)

        # Установка связи между пользователями
        user.partner_id = partner.id
        partner.partner_id = user.id

        # Отправка сообщения партнерам
        await send_partner_found_message(user.id, state)
        await send_partner_found_message(partner.id, partner_state)

        # Установка состояния messaging для партнера
        # получаем текущее состояние партнера (то, что обычно передается в аргументе state)
        await state.set_state(OurStates.messaging)  # Установка состояния messaging
        await partner_state.set_state(OurStates.messaging)  # Установка состояния messaging для партнера

        # Удалить кнопку "Познакомиться"
        await remove_meet_message(user_id, state)
        await remove_meet_message(partner.id, partner_state)

    else:
        await message.answer(
            text="Пока никого нет, кто был бы свободен. Подожди немного."
        )

    if isinstance(message, types.CallbackQuery):
        await call.message.delete_reply_markup()
        await bot.answer_callback_query(call.id)


async def send_partner_found_message(user_id: int, state: FSMContext):
    # Отправить сообщение о том, что собеседник найден
    partner_id = user_mapping[user_id].partner_id
    partner = user_mapping[partner_id]

    to_user = await bot.send_message(
        chat_id=user_id,
        text=f"Ты сейчас связан с {partner.name}! Напиши что-нибудь.",
        reply_markup=skip_kb_inline,
    )
    await state.update_data(connect_with_message=to_user.message_id)


async def remove_meet_message(user_id: int, state: FSMContext):
    # Удалить кнопку сообщение с кнопкой "Познакомиться"
    partner_data = await state.get_data()
    meet_with_message = partner_data.get("meet_with_message")  # это сообщение должно быть заранее сохранено в состоянии
    if meet_with_message:
        await bot.delete_message(
            chat_id=user_id, message_id=meet_with_message
        )
    await state.update_data(meet_with_message=None)


async def get_state_by_id(user_id: int) -> FSMContext:
    # Получить состояние по идентификатору пользователя
    return dp.get_current().current_state(chat=user_id, user=user_id)


@dp.callback_query_handler(skip_callback_data.filter(), state=OurStates.messaging)
@dp.message_handler(
    Text(equals="🔎 Найти другого собеседника", ignore_case=True), state=OurStates.messaging
)
async def skip_handler(message: types.Message | types.CallbackQuery, state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        call = message
        await bot.answer_callback_query(call.id)
        # удалить кнопку
        await bot.edit_message_reply_markup(
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=None,
        )

    user = user_mapping[message.from_user.id]
    partner_id = user.partner_id
    partner_state = await get_state_by_id(partner_id)

    # Отправка сообщения пользователям
    to_user = await bot.send_message(
        chat_id=user.id,
        text="Хорошо, пропускаем текущего партнера.",
        reply_markup=greeting_kb
    )
    await state.update_data(meet_with_message=to_user.message_id)

    to_partner = await bot.send_message(
        chat_id=partner_id,
        text="Твой партнер дропнул тебя ;6",
        reply_markup=greeting_kb,
    )
    await partner_state.update_data(meet_with_message=to_partner.message_id)

    # Удаление связи между пользователями
    user.partner_id = None
    partner = user_mapping[partner_id]
    partner.partner_id = None

    # Установка состояния wait_for_partner для партнера
    await OurStates.wait_for_partner.set()  # текущему пользователю
    await partner_state.set_state(OurStates.wait_for_partner)  # партнеру


@dp.message_handler(
    state=OurStates.messaging  # будет работать только в состоянии messaging
)  # Обработчик для обмена сообщениями между пользователями
async def messaging_handler(message: types.Message):
    user = user_mapping[message.from_id]  # Получение объекта пользователя
    partner_id = user.partner_id  # Получение идентификатора партнера
    text = f"*{user.name}*\n {message.text}"  # Формирование текста сообщения
    await dp.bot.send_message(
        chat_id=partner_id, text=text, parse_mode="MarkdownV2"
    )  # Отправка сообщения партнеру


@dp.message_handler(
    content_types=types.ContentType.PHOTO,  # будет работать только если сообщение является фотографией
    state=OurStates.messaging,  # будет работать только в состоянии messaging
)  # Обработчик для обмена фотографиями между пользователями
async def messaging_photo_handler(message: types.Message):
    user = user_mapping[message.from_id]
    partner_id = user.partner_id

    # Получение объекта фотографии
    photo = message.photo[-1]

    new_caption = f"**{user.name}:**\n {message.caption}"  # Формирование текста сообщения
    await dp.bot.send_photo(
        chat_id=partner_id, photo=photo.file_id, caption=new_caption
    )  # Отправка фотографии партнеру


@dp.message_handler(
    content_types=types.ContentType.VIDEO,  # будет работать только если сообщение является видео
    state=OurStates.messaging,  # будет работать только в состоянии messaging
)
async def messaging_video_handler(message: types.Message):
    user = user_mapping[message.from_id]
    partner_id = user.partner_id

    # Получение объекта видео
    video = message.video

    new_caption = f"**{user.name}**:\n {message.caption}"  # Формирование текста сообщения
    await dp.bot.send_video(
        chat_id=partner_id, video=video.file_id, caption=new_caption
    )  # Отправка видео партнеру


@dp.message_handler(
    content_types=types.ContentType.STICKER,  # будет работать только если сообщение является стикером
    state=OurStates.messaging,  # будет работать только в состоянии messaging
)
async def messaging_sticker_handler(message: types.Message):
    user = user_mapping[message.from_id]
    partner_id = user.partner_id

    # Получение объекта стикера
    sticker = message.sticker

    new_caption = f"**{user.name}**:\n"  # Формирование подписи с именем отправителя
    await dp.bot.send_message(
        chat_id=partner_id, text=new_caption
    )  # Отправка подписи партнеру
    await dp.bot.send_sticker(
        chat_id=partner_id, sticker=sticker.file_id
    )  # Отправка стикера партнеру с подписью


@dp.message_handler(
    content_types=types.ContentType.AUDIO,  # будет работать только если сообщение является аудио
    state=OurStates.messaging,  # будет работать только в состоянии messaging
)
async def messaging_audio_handler(message: types.Message):
    user = user_mapping[message.from_id]
    partner_id = user.partner_id

    # Получение объекта аудио
    audio = message.audio

    new_caption = f"**{user.name}:**\n"  # Формирование текста сообщения
    if message.caption:
        new_caption += f" {message.caption}"
    await dp.bot.send_audio(
        chat_id=partner_id, audio=audio.file_id, caption=new_caption
    )  # Отправка аудио партнеру


if __name__ == "__main__":
    # Запуск бота
    executor.start_polling(dispatcher=dp, skip_updates=True)
