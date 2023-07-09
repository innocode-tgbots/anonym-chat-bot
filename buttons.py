from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

greeting_kb = ReplyKeyboardMarkup(resize_keyboard=True)
greeting_bt = KeyboardButton("👋 Познакомиться")
greeting_kb.add(greeting_bt)
