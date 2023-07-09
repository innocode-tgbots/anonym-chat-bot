# # Менюшные кнопки
# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
#
# greeting_kb = ReplyKeyboardMarkup(resize_keyboard=True)
# greeting_bt = KeyboardButton("👋 Познакомиться")
# greeting_kb.add(greeting_bt)


# Инлайн кнопки
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

greeting_callback_data = CallbackData("greeting")

greeting_kb = InlineKeyboardMarkup(row_width=1)
greeting_bt = InlineKeyboardButton("👋 Познакомиться",
                                   callback_data=greeting_callback_data.new())
greeting_kb.add(greeting_bt)
