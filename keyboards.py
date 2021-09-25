from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class Keyboards:
    def __init__(self, kb_texts: dict):
        self.kb_texts = kb_texts

        self.menu = InlineKeyboardMarkup()
        self.menu.add(InlineKeyboardButton(self.kb_texts['status'], callback_data='ashyq_status'))

        self.to_menu = InlineKeyboardMarkup()
        self.to_menu.add(InlineKeyboardButton(self.kb_texts['to_menu'], callback_data='menu'))

        self.ashyq = InlineKeyboardMarkup()
        self.ashyq.add(InlineKeyboardButton(self.kb_texts['update'], callback_data='ashyq_status'))
        self.ashyq.add(InlineKeyboardButton(self.kb_texts['untie'], callback_data='ashyq_untie'))

        for row in self.to_menu.inline_keyboard:
            self.ashyq.inline_keyboard.append(row)

        self.cancel = InlineKeyboardMarkup()
        self.cancel.add(InlineKeyboardButton(self.kb_texts['cancel'], callback_data='cancel'))
