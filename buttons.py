# Инлайн кнопки
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.callback_data import CallbackData

greeting_callback_data = CallbackData("greeting")

greeting_kb = InlineKeyboardMarkup(row_width=1)
greeting_bt = InlineKeyboardButton(
    "👋 Познакомиться", callback_data=greeting_callback_data.new()
)
greeting_kb.add(greeting_bt)

# Менюшные кнопки
skip_kb_menu = ReplyKeyboardMarkup(resize_keyboard=True)
skip_kb_menu.add(KeyboardButton(text="🔎 Найти другого собеседника"))

skip_callback_data = CallbackData("skip")

skip_kb_inline = InlineKeyboardMarkup(row_width=1)
skip_bt_inline = InlineKeyboardButton(
    text="🔎 Найти другого собеседника", callback_data=skip_callback_data.new()
)
skip_kb_inline.add(skip_bt_inline)
