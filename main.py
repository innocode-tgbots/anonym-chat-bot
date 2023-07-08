from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text

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
async def enter_name_handler(message: types.Message):
    user_id = message.from_id
    user = user_mapping[user_id]
    user.name = message.text  # Сохранение введенного имени пользователя

    text = f"Отлично, {user.name}! Сейчас я попробую найти тебе пару."
    await message.answer(text=text)
    await message.answer(text="Ты готов? Напиши 'да', если да, и 'нет', если нет.")
    await OurStates.yes_or_no.set()  # Установка состояния yes_or_no


@dp.message_handler(
    Text(equals=("да", "yes"), ignore_case=True),
    # будет работать только если текст сообщения равен "да" или "yes"
    state=OurStates.yes_or_no  # будет работать только в состоянии yes_or_no
)  # Обработчик для ответа "да"
async def wait_for_partner_handler(message: types.Message, ):
    await OurStates.wait_for_partner.set()  # Установка состояния wait_for_partner

    user = user_mapping[message.from_id]
    chosen = None  # Переменная для хранения идентификатора партнера

    # Поиск свободного партнера среди пользователей в словаре
    for partner_id, partner_obj in user_mapping.items():
        # Проверка, что пользователь не связан с самим собой
        # и что у партнера нет связи с другим пользователем
        if partner_id != user.user_id and partner_obj.partner_id is None and partner_obj.name is not None:
            # Получение текущего контекста партнера
            partner_context = dp.get_current().current_state(chat=partner_id, user=partner_id)
            # Где он находится на графе состояний
            partner_state = await partner_context.get_state()
            # Если он в состоянии "ожидает партнера", то выбираем его
            if partner_state == OurStates.wait_for_partner.state:
                chosen = partner_id
                break

    if chosen is not None:
        # Установка связи между пользователями
        partner = user_mapping[chosen]

        user.partner_id = chosen
        partner.partner_id = user.user_id

        await message.answer(
            text=f"Ты сейчас связан с {user_mapping[chosen].name}! Напиши что-нибудь."
        )
        # отправка сообщения партнеру
        await dp.bot.send_message(
            chat_id=chosen, text=f"Ты сейчас связан с {user.name}! Напиши что-нибудь."
        )

        await OurStates.messaging.set()  # Установка состояния messaging

        # Установка состояния messaging для партнера
        # получаем текущее состояние партнера (то, что обычно передается в аргументе state)
        partner_state = dp.get_current().current_state(chat=chosen, user=chosen)
        await partner_state.set_state(OurStates.messaging)  # Установка состояния messaging для партнера
    else:
        await message.answer(
            text="Пока никого нет, кто был бы свободен. Подожди немного."
        )


@dp.message_handler(
    state=OurStates.messaging  # будет работать только в состоянии messaging
)  # Обработчик для обмена сообщениями между пользователями
async def messaging_handler(message: types.Message):
    user = user_mapping[message.from_id]  # Получение объекта пользователя
    partner_id = user.partner_id  # Получение идентификатора партнера
    text = f"{user.name}: {message.text}"  # Формирование текста сообщения
    await dp.bot.send_message(chat_id=partner_id, text=text)  # Отправка сообщения партнеру


if __name__ == "__main__":
    # Запуск бота
    executor.start_polling(dispatcher=dp, skip_updates=True)
