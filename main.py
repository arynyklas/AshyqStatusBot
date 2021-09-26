from aiogram import Bot, Dispatcher, types, filters, exceptions, executor
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher.handler import CancelHandler
from db import DataBase
from keyboards import Keyboards
from time import time
from asyncio import sleep
from config import bot_token, db_uri, db_name, owners, texts, yes_words, chars

import ashyq


db = DataBase(db_uri, db_name)

bot = Bot(bot_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MongoStorage(db_name=db_name, uri=db_uri))

keyboards = Keyboards(texts['keyboards'])

owners_filter = filters.IDFilter(owners)


class AshyqForm(StatesGroup):
    phone_number = State()
    sms_code = State()

class AdminForm(StatesGroup):
    mailing = State()
    mailing_forward = State()


class Middleware(BaseMiddleware):
    def __init__(self):
        super(Middleware, self).__init__()

    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message.chat.type != types.ChatType.PRIVATE:
            raise CancelHandler

        user = db.get_user(message.from_user.id)

        if not user:
            db.add_user(message.from_user.id)
            user = db.get_user(message.from_user.id)

        if not user['ashyq'] and not await dp.current_state(user=user['user_id']).get_state():
            await AshyqForm.phone_number.set()

            await message.answer(
                '{}\n\n{}'.format(
                    texts['start'],
                    texts['enter_phone_number']
                )
            )

            raise CancelHandler


@dp.callback_query_handler(state='*')
async def callback_query_handler(callback_query: types.CallbackQuery, state: FSMContext):
    args = callback_query.data.split('_')

    user = db.get_user(callback_query.from_user.id)

    if args[0] == 'cancel':
        await state.finish()

        await callback_query.message.edit_text(
            texts['cancelled'],
            reply_markup=keyboards.to_menu
        )

    elif args[0] == 'menu':
        if not user['ashyq'] and not await dp.current_state(user=user['user_id']).get_state():
            await callback_query.message.delete()

            await AshyqForm.phone_number.set()

            await callback_query.message.answer(
                '{}\n\n{}'.format(
                    texts['start'],
                    texts['enter_phone_number']
                )
            )

            raise CancelHandler

        else:
            await callback_query.message.edit_text(
                texts['start'],
                reply_markup=keyboards.menu
            )

    elif args[0] == 'ashyq':
        if args[1] == 'status':
            _ashyq = ashyq.Ashyq(
                driver       = ashyq.drivers.sync.SyncDriver(),
                phone_number = user['ashyq']['phone_number'],
                device_id    = user['ashyq']['device_id']
            )

            _ashyq.access_token = user['ashyq']['access_token']
            _ashyq.refresh_token = user['ashyq']['refresh_token']

            try:
                check: ashyq.types.Check = _ashyq.user_pcr()

            except ashyq.exceptions.AshyqException:
                user['ashyq'] = {}
                db.edit_user(user['user_id'], user)

                await callback_query.message.edit_text(
                    texts['incorrect_account'],
                    reply_markup=keyboards.to_menu
                )

                await callback_query.answer()
                return

            if user['ashyq']['access_token'] != _ashyq.access_token:
                user['ashyq']['access_token']  = _ashyq.access_token
                user['ashyq']['refresh_token'] = _ashyq.refresh_token
                db.edit_user(user['user_id'], user)

            await callback_query.message.edit_text(
                texts['ashyq'].format(
                    phone_number       = _ashyq.phone_number,
                    char               = chars[check._pass],
                    status             = check.status,
                    status_description = check.status_description,
                    date               = check.date
                ),
                reply_markup=keyboards.ashyq
            )

        elif args[1] == 'untie':
            user['ashyq'] = {}
            db.edit_user(user['user_id'], user)

            await callback_query.message.edit_text(
                texts['account_untied'],
                reply_markup=keyboards.to_menu
            )

    await callback_query.answer()


@dp.message_handler(commands=['start'])
async def start_command_handler(message: types.Message):
    await message.answer(
        texts['start'],
        reply_markup=keyboards.menu
    )


@dp.message_handler(commands=['status'])
async def status_command_handler(message: types.Message):
    user = db.get_user(message.from_user.id)

    _ashyq = ashyq.Ashyq(
        driver       = ashyq.drivers.sync.SyncDriver(),
        phone_number = user['ashyq']['phone_number'],
        device_id    = user['ashyq']['device_id']
    )

    _ashyq.access_token = user['ashyq']['access_token']
    _ashyq.refresh_token = user['ashyq']['refresh_token']

    try:
        check: ashyq.types.Check = _ashyq.user_pcr()

    except ashyq.exceptions.AshyqException:
        user['ashyq'] = {}
        db.edit_user(user['user_id'], user)

        await message.answer(
            texts['incorrect_account'],
            reply_markup=keyboards.to_menu
        )

        return

    if user['ashyq']['access_token'] != _ashyq.access_token:
        user['ashyq']['access_token']  = _ashyq.access_token
        user['ashyq']['refresh_token'] = _ashyq.refresh_token
        db.edit_user(user['user_id'], user)

    await message.answer(
        texts['ashyq'].format(
            phone_number       = _ashyq.phone_number,
            char               = chars[check._pass],
            status             = check.status,
            status_description = check.status_description,
            date               = check.date
        ),
        reply_markup=keyboards.ashyq
    )


@dp.message_handler(state=AshyqForm.phone_number)
async def enter_phone_number_handler(message: types.Message, state: FSMContext):
    phone_number = message.text

    _ashyq = ashyq.Ashyq(
        driver       = ashyq.drivers.sync.SyncDriver(),
        phone_number = phone_number
    )

    _ashyq.new_install()

    await state.set_data({
        'phone_number': phone_number,
        'device_id': _ashyq.device_id
    })

    await AshyqForm.sms_code.set()

    await message.answer(texts['enter_sms_code'], reply_markup=keyboards.cancel)


@dp.message_handler(state=AshyqForm.sms_code)
async def enter_sms_code_handler(message: types.Message, state: FSMContext):
    sms_code = message.text

    data = await state.get_data()

    _ashyq = ashyq.Ashyq(
        driver       = ashyq.drivers.sync.SyncDriver(),
        phone_number = data['phone_number'],
        device_id    = data['device_id']
    )

    try:
        connect: ashyq.types.Connect = _ashyq.connect(sms_code)

    except ashyq.exceptions.AshyqException:
        await state.finish()

        await message.answer(
            texts['incorrect_account'],
            reply_markup=keyboards.to_menu
        )

        return

    await state.finish()

    user = db.get_user(message.from_user.id)
    user['ashyq']['device_id']     = data['device_id']
    user['ashyq']['phone_number']  = data['phone_number']
    user['ashyq']['access_token']  = connect.access_token
    user['ashyq']['refresh_token'] = connect.refresh_token
    db.edit_user(user['user_id'], user)

    await message.answer(texts['account_tied'], reply_markup=keyboards.to_menu)


@dp.message_handler(owners_filter, commands=['mailing'], state='*')
async def mailing_command_handler(message: types.Message, state: FSMContext):
    await state.finish()

    await AdminForm.mailing.set()

    await message.answer(
        texts['send_mailing_message'],
        reply_markup=keyboards.cancel
    )


@dp.message_handler(content_types=types.ContentType.ANY, state=AdminForm.mailing)
async def process_mailing_handler(message: types.Message, state: FSMContext):
    await state.set_data({'message': message.to_python()})

    await AdminForm.mailing_forward.set()

    await message.answer(
        texts['set_mailing_foward'].format(
            yes_words = '/'.join(yes_words)
        ),
        reply_markup  = keyboards.cancel
    )


@dp.message_handler(content_types=types.ContentType.ANY, state=AdminForm.mailing_forward)
async def process_mailing_forward_handler(message: types.Message, state: FSMContext):
    total = 0
    sent = 0
    unsent = 0

    message_text = message.text.lower()

    data = await state.get_data()
    _message = types.Message.to_object(data['message'])

    is_forward = False

    for word in yes_words:
        if message_text == word:
            is_forward = True

    func = _message.forward if is_forward else _message.copy_to
    kwargs = {} if is_forward else {'reply_markup': keyboards.to_menu}

    await state.finish()
    await message.answer(texts['mailing_started'])

    start = time()

    for user in db.get_user():
        kwargs['chat_id'] = user['user_id']

        try:
            await func(**kwargs)

            sent += 1

        except:
            unsent += 1

        total += 1

        await sleep(0.04)

    await _message.reply(
        texts['mailing_stats'].format(
            total=total,
            sent=sent,
            unsent=unsent,
            time=round(time() - start, 2)
        )
    )


@dp.message_handler(content_types=types.ContentType.ANY, state='*')
async def any_handler(message: types.Message, state: FSMContext):
    await message.answer(texts['not_understand'])


dp.middleware.setup(Middleware())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
