from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, User


class Keyboards:
    def __init__(self, kb_texts: dict, me: User):
        self.kb_texts = kb_texts
        self._me = me

        self.menu = InlineKeyboardMarkup()
        self.menu.add(InlineKeyboardButton(
            self.kb_texts['status'],
            callback_data='ashyq_status'
        ))

        self.to_menu = InlineKeyboardMarkup()
        self.to_menu.add(InlineKeyboardButton(
            self.kb_texts['to_menu'],
            callback_data='menu'
        ))

        self.ashyq = InlineKeyboardMarkup()
        self.ashyq.add(InlineKeyboardButton(
            self.kb_texts['update'],
            callback_data='ashyq_status'
        ))
        self.ashyq.add(InlineKeyboardButton(
            self.kb_texts['untie'],
            callback_data='ashyq_untie'
        ))

        for row in self.to_menu.inline_keyboard:
            self.ashyq.inline_keyboard.append(row)

        self.cancel = InlineKeyboardMarkup()
        self.cancel.add(InlineKeyboardButton(
            self.kb_texts['cancel'],
            callback_data='cancel'
        ))

        self.tie_account = InlineKeyboardMarkup()
        self.tie_account.add(InlineKeyboardButton(
            self.kb_texts['tie'],
            url='https://t.me/{}?start=tie'.format(self._me.username)
        ))

    def ashyq_inline(self, user_id: int):
        markup = InlineKeyboardMarkup()

        markup.add(InlineKeyboardButton(
            self.kb_texts['update'],
            callback_data='ashyq_status_{}'.format(user_id)
        ))

        markup.add(InlineKeyboardButton(
            self.kb_texts['untie'],
            callback_data='ashyq_untie_{}'.format(user_id)
        ))

        return markup
