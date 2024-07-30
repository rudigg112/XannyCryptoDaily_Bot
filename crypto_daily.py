import os

import aiohttp
from aiogram import Bot, Dispatcher, types
import asyncio
import logging

from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.types import FSInputFile, CallbackQuery

from db_main import *
from aiogram.filters.command import Command

from keyboards import *

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(loop=loop)


@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    user_id = message.from_user.id

    if user_id in admin_ids:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

        text_subs = load_text_subs_admin()

        db = DBClient()
        _SQL = 'SELECT name_app, callback_data FROM apps'
        result = db.select_fetchall(_SQL)
        db.exit_db()

        keyboard = create_keyboard_from_result_admin(result)

        await bot.send_message(chat_id=message.chat.id,
                               text=f"Админ-панель:\n\n{text_subs}",
                               reply_markup=keyboard, parse_mode="Markdown")


@dp.callback_query(lambda c: c.data.startswith('admin_panel'))
async def handle_app_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in admin_ids:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

        text_subs = load_text_subs_admin()

        db = DBClient()
        _SQL = 'SELECT name_app, callback_data FROM apps'
        result = db.select_fetchall(_SQL)
        db.exit_db()

        keyboard = create_keyboard_from_result_admin(result)

        await bot.send_message(chat_id=callback.message.chat.id,
                               text=f"Админ-панель:\n\n{text_subs}",
                               reply_markup=keyboard, parse_mode="Markdown")


@dp.callback_query(lambda c: c.data.startswith('edit_'))
async def handle_app_selection(callback: CallbackQuery):
    app_callback_data = callback.data[len('edit_'):]

    text, edit_keyboard = load_text_app_admin(app_callback_data)

    await callback.message.edit_text(text=text, reply_markup=edit_keyboard)


@dp.callback_query(lambda c: c.data.startswith('change_status_'))
async def change_status(callback: CallbackQuery):
    app_id = callback.data[len('change_status_'):]

    db = DBClient()
    query_select = 'SELECT is_available FROM apps WHERE id = %s'
    is_available = db.select_fetchone(query_select, (app_id,))[0]

    new_status = 0 if is_available else 1
    query_update = 'UPDATE apps SET is_available = %s WHERE id = %s'
    db.update_value_in_database(query_update, (new_status, app_id))

    db.exit_db()

    text, edit_keyboard = load_text_app_admin_id(app_id)

    await callback.message.edit_text(text=text, reply_markup=edit_keyboard)


@dp.callback_query(lambda c: c.data.startswith('change_name_'))
async def change_name(callback: CallbackQuery):
    app_id = callback.data[len('change_name_'):]
    mes = await callback.message.answer(f"Введите новое название для приложения:")

    @dp.message()
    async def update_name(message: types.Message):
        new_name = message.text
        db = DBClient()
        query_update = 'UPDATE apps SET name_app = %s WHERE id = %s'
        db.update_value_in_database(query_update, (new_name, app_id))

        db.exit_db()

        text, edit_keyboard = load_text_app_admin_id(app_id)

        await callback.message.edit_text(text=text, reply_markup=edit_keyboard)

        try:
            await mes.delete()
        except TelegramBadRequest:
            pass
        await message.delete()


@dp.callback_query(lambda c: c.data.startswith('change_link_'))
async def change_link(callback: CallbackQuery):
    app_id = callback.data[len('change_link_'):]
    mes = await callback.message.answer(f"Введите новую ссылку для приложения:")

    @dp.message()
    async def update_link(message: types.Message):
        new_link = message.text
        db = DBClient()
        query_update = 'UPDATE apps SET link = %s WHERE id = %s'
        db.update_value_in_database(query_update, (new_link, app_id))

        db.exit_db()

        text, edit_keyboard = load_text_app_admin_id(app_id)

        await callback.message.edit_text(text=text, reply_markup=edit_keyboard)

        try:
            await mes.delete()
        except TelegramBadRequest:
            pass
        await message.delete()


@dp.callback_query(lambda c: c.data.startswith('change_text_'))
async def change_code_text(callback: CallbackQuery):
    app_id = callback.data[len('change_text_'):]
    mes = await callback.message.answer(f"Введите текстовый код для приложения:")
    print(f'198, change_code_text {app_id}')

    @dp.message()
    async def update_text_code(message: types.Message):
        new_link = message.text
        db = DBClient()
        query_update = 'UPDATE apps SET code_text = %s WHERE id = %s'
        db.update_value_in_database(query_update, (new_link, app_id))

        db.exit_db()

        text, edit_keyboard = load_text_app_admin_id(app_id)

        await callback.message.edit_text(text=text, reply_markup=edit_keyboard)

        try:
            await mes.delete()
        except TelegramBadRequest:
            pass
        await message.delete()


# Обработка изменения изображения приложения
@dp.callback_query(lambda c: c.data.startswith('change_image_'))
async def change_image(callback: CallbackQuery):
    app_id = callback.data[len('change_image_'):]
    mes = await callback.message.answer(f"Отправьте новое изображение для приложения ID {app_id}:")

    @dp.message()
    async def update_image(message: types.Message):
        photo_id = message.photo[-1].file_id
        file_name = f"app_{app_id}.jpg"
        file_path = os.path.join(IMAGE_FOLDER, file_name)

        os.makedirs(IMAGE_FOLDER, exist_ok=True)

        await download_and_save_photo(photo_id, file_path)

        db = DBClient()
        db.exit_db()

        text, edit_keyboard = load_text_app_admin_id(app_id)

        await callback.message.edit_text(text=text, reply_markup=edit_keyboard)

        try:
            await mes.delete()
        except TelegramBadRequest:
            pass
        await message.delete()


@dp.callback_query(lambda c: c.data.startswith('change_video_'))
async def change_video(callback: CallbackQuery):
    app_id = callback.data[len('change_video_'):]
    mes = await callback.message.answer(f"Отправьте новое видео для приложения ID {app_id}:")

    @dp.message()
    async def update_video(message: types.Message):
        video_id = message.video.file_id
        file_name = f"app_{app_id}.mp4"
        file_path = os.path.join(IMAGE_FOLDER, file_name)

        os.makedirs(IMAGE_FOLDER, exist_ok=True)

        await download_and_save_video(video_id, file_path)

        db = DBClient()
        db.exit_db()

        text, edit_keyboard = load_text_app_admin_id(app_id)

        await callback.message.edit_text(text=text, reply_markup=edit_keyboard)

        try:
            await mes.delete()
        except TelegramBadRequest:
            pass
        await message.delete()


@dp.callback_query(lambda c: c.data.startswith('mail_me_'))
async def change_video(callback: CallbackQuery):
    app_id = callback.data[len('mail_me_'):]

    db = DBClient()
    _sql = 'SELECT name_app, link, code_text FROM apps WHERE id = %s'
    result = db.select_fetchone(_sql, (app_id,))
    db.exit_db()

    text_code = f'ТЕСТОВАЯ РАССЫЛКА\n\nЕжедневный код:\n\n {result[2]}'
    text_image = 'ТЕСТОВАЯ РАССЫЛКА\n\nКартинка'
    text_video = 'ТЕСТОВАЯ РАССЫЛКА\n\nВидео'

    image_path = os.path.join(IMAGE_FOLDER, f'app_{app_id}.jpg')
    video_path = os.path.join(IMAGE_FOLDER, f'app_{app_id}.mp4')

    await bot.send_message(callback.message.chat.id, text_code)

    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(callback.message.chat.id, photo, caption=text_image)

    if os.path.exists(video_path):
        video = FSInputFile(video_path)
        await bot.send_video(callback.message.chat.id, video, caption=text_video)



@dp.callback_query(lambda c: c.data.startswith('mail_image_'))
async def mail_image_all(callback: CallbackQuery):
    app_id = callback.data[len('mail_image_'):]

    image_path = os.path.join(IMAGE_FOLDER, f'app_{app_id}.jpg')

    if os.path.exists(image_path):
        db = DBClient()
        _sql = 'SELECT telegram_id FROM subs WHERE app_obj_id = %s'
        result = db.select_fetchall(_sql, (app_id,))
        db.exit_db()

        total_users = len(result)
        successful_sends = 0
        failed_sends = 0

        text_image = 'ТЕСТОВАЯ РАССЫЛКА\n\nКартинка'
        photo = FSInputFile(image_path)

        for user in result:
            user_id = user[0]
            try:
                await bot.send_photo(chat_id=user_id, photo=photo, caption=text_image)
                successful_sends += 1
            except TelegramAPIError:
                failed_sends += 1

        stats_message = (
            f"Рассылка завершена.\n"
            f"Всего пользователей: {total_users}\n"
            f"Успешно отправлено: {successful_sends}\n"
            f"Не отправлено: {failed_sends}"
        )
        await bot.send_message(chat_id=callback.message.chat.id, text=stats_message)
    else:
        await bot.send_message(chat_id=callback.message.chat.id, text="Изображение не найдено.")


@dp.callback_query(lambda c: c.data.startswith('mail_video_'))
async def mail_video(callback: CallbackQuery):
    app_id = callback.data[len('mail_video_'):]

    video_file = os.path.join(IMAGE_FOLDER, f"app_{app_id}.mp4")

    if os.path.exists(video_file):
        db = DBClient()
        _sql = 'SELECT telegram_id FROM subs WHERE app_obj_id = %s'
        result = db.select_fetchall(_sql, (app_id,))
        db.exit_db()

        total_users = len(result)
        successful_sends = 0
        failed_sends = 0

        text_image = 'ТЕСТОВАЯ РАССЫЛКА\n\nВИДЕО'
        video = FSInputFile(video_file)

        for user in result:
            user_id = user[0]
            try:
                await bot.send_video(chat_id=user_id, video=video, caption=text_image)
                successful_sends += 1
            except TelegramAPIError:
                failed_sends += 1

        stats_message = (
            f"Рассылка завершена.\n"
            f"Всего пользователей: {total_users}\n"
            f"Успешно отправлено: {successful_sends}\n"
            f"Не отправлено: {failed_sends}"
        )
        await bot.send_message(chat_id=callback.message.chat.id, text=stats_message)
    else:
        await bot.send_message(chat_id=callback.message.chat.id, text="Изображение не найдено.")


@dp.callback_query(lambda c: c.data.startswith('mail_text_'))
async def mail_video(callback: CallbackQuery):
    app_id = callback.data[len('mail_text_'):]

    db = DBClient()
    _sql = 'SELECT code_text FROM apps WHERE id = %s'
    result = db.select_fetchone(_sql, (app_id,))
    print(result)
    if result is not None:
        _sql = 'SELECT telegram_id FROM subs WHERE app_obj_id = %s'
        result_users = db.select_fetchall(_sql, (app_id,))

        total_users = len(result_users)
        successful_sends = 0
        failed_sends = 0
        text_to_send = f'{result[0]}'
        print(result_users)
        for user in result_users:
            print(user)
            user_id = user[0]
            try:
                await bot.send_message(chat_id=user_id, text=text_to_send)
                successful_sends += 1
            except TelegramAPIError:
                failed_sends += 1

        # Отправка статистики
        stats_message = (
            f"Рассылка завершена.\n"
            f"Всего пользователей: {total_users}\n"
            f"Успешно отправлено: {successful_sends}\n"
            f"Не отправлено: {failed_sends}"
        )
        await bot.send_message(chat_id=callback.message.chat.id, text=stats_message)

    db.exit_db()


async def download_and_save_photo(file_id, file_path):
    file = await bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    print(file_url)
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with open(file_path, 'wb') as f:
                    f.write(await resp.read())


async def download_and_save_video(file_id, file_path):
    file = await bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    print(file_url)
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with open(file_path, 'wb') as f:
                    f.write(await resp.read())


@dp.message(Command("start"))
async def ban_user(message: types.Message):
    photo = FSInputFile('files/start_photo.jpeg')
    caption = (f'👋 Привет, {message.from_user.first_name}!\n\n'
               f'Этот бот создан для тех, кто не хочет тратить свое время ⏳ на поиск ежедневных кодов для тапалок!\n\n'
               f'🗓 Актуальные коды для нужных тебе приложений будут отправляться этим ботом ежедневно!')
    markup = menu_open
    await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=caption, reply_markup=markup)
    await message.delete()


@dp.callback_query(lambda c: c.data == 'menu_open')
async def menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)

    if chat_member.status in ['member', 'administrator', 'creator']:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        db = DBClient()
        _SQL = 'SELECT name_app, callback_data FROM apps WHERE is_available = 1'
        result = db.select_fetchall(_SQL, )
        db.exit_db()

        keyboard = create_keyboard_from_result(result)

        text_subs = load_text_subs(callback.from_user.id)

        await bot.send_message(chat_id=callback.message.chat.id,
                               text="Выбрать тапалки, коды которых хочешь получать\n\n"
                                    f"{text_subs}",
                               reply_markup=keyboard, parse_mode="Markdown")
    else:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await bot.send_message(chat_id=callback.message.chat.id,
                               text="Для использования этого бота вы должны быть подписаны на наш канал.",
                               reply_markup=subscribe_button)


@dp.callback_query(lambda c: c.data == 'sub_on_channel_confirmed')
async def ty_for_follow(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)

    if chat_member.status in ['member', 'administrator', 'creator']:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        db = DBClient()
        _SQL = 'SELECT name_app, callback_data FROM apps WHERE is_available = 1'
        result = db.select_fetchall(_SQL, )
        db.exit_db()

        keyboard = create_keyboard_from_result(result)

        text_subs = load_text_subs(callback.from_user.id)

        await bot.send_message(chat_id=callback.message.chat.id,
                               text="Теперь ты можешь выбрать коды тапалок, которые хочешь получать\n\n"
                                    f"{text_subs}",
                               reply_markup=keyboard, parse_mode="Markdown")
    else:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await bot.send_message(chat_id=callback.message.chat.id,
                               text="Для использования этого бота ты должен быть подписан на наш канал.",
                               reply_markup=subscribe_button)


@dp.callback_query(lambda c: c.data.startswith('app_'))
async def handle_app_selection(callback: CallbackQuery):
    selected_app = callback.data

    db = DBClient()

    text = db.check_subs(selected_app, callback.from_user.id)

    _SQL = 'SELECT name_app, callback_data FROM apps WHERE is_available = 1'
    result = db.select_fetchall(_SQL, )

    keyboard = create_keyboard_from_result(result)

    text_subs = load_text_subs(callback.from_user.id)

    db.exit_db()

    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await bot.send_message(chat_id=callback.message.chat.id,
                           text=f'{text}\n\n{text_subs}',
                           reply_markup=keyboard, parse_mode="Markdown")


def create_keyboard_from_result(result):
    keyboard = []
    for app_name, callback_data in result:
        button = InlineKeyboardButton(text=app_name, callback_data=callback_data)
        keyboard.append(button)

    rows = [keyboard[i:i + 2] for i in range(0, len(keyboard), 2)]

    return InlineKeyboardMarkup(inline_keyboard=rows)


def create_keyboard_from_result_admin(result):
    keyboard = []
    for app_name, callback_data in result:
        button = InlineKeyboardButton(text=app_name, callback_data=f'edit_{callback_data}')
        keyboard.append(button)

    rows = [keyboard[i:i + 2] for i in range(0, len(keyboard), 2)]

    return InlineKeyboardMarkup(inline_keyboard=rows)


def load_text_subs(telegram_id):
    db = DBClient()

    query_select = 'SELECT id, name_app, link, callback_data FROM apps WHERE is_available = 1'
    result_all_apps = db.select_fetchall(query_select, )

    query_user_subs = 'SELECT app_obj_id FROM subs WHERE telegram_id = %s'
    result_user_subs = db.select_fetchall(query_user_subs, (telegram_id,))

    db.exit_db()

    app_ids_subscribed = {row[0] for row in result_user_subs}
    app_statuses = []

    for app in result_all_apps:
        app_id = app[0]
        app_name = app[1]
        app_link = app[2]
        if app_id in app_ids_subscribed:
            status = 'подписка оформлена ✅'
        else:
            status = 'подписка не оформлена ⛔'
        app_statuses.append(f"[{app_name}]({app_link}) - {status}")

    return '\n'.join(app_statuses)


def load_text_subs_admin():
    db = DBClient()

    query_select = 'SELECT id, name_app, link, callback_data, is_available, code_text FROM apps'
    result_all_apps = db.select_fetchall(query_select)

    db.exit_db()

    app_statuses = []
    for app in result_all_apps:
        app_id = app[0]
        app_name = app[1]
        app_link = app[2]
        is_available = app[4]
        code_text = app[5]
        status = "активно" if is_available == 1 else "не активно"

        photo_file = os.path.join(IMAGE_FOLDER, f"app_{app_id}.jpg")
        video_file = os.path.join(IMAGE_FOLDER, f"app_{app_id}.mp4")

        photo_exists = os.path.isfile(photo_file)
        video_exists = os.path.isfile(video_file)

        app_info = (f"[{app_name}]({app_link}) - {status}\n"
                    f"Code Text: {code_text}\n"
                    f"Фото: {'есть' if photo_exists else 'отсутствует'}\n"
                    f"Видео: {'есть' if video_exists else 'отсутствует'}\n")

        app_statuses.append(app_info)

    return '\n'.join(app_statuses)


def load_text_app_admin(app_callback_data):
    db = DBClient()
    query_select = 'SELECT id, name_app, link, is_available, code_text FROM apps WHERE callback_data = %s'
    app_data = db.select_fetchone(query_select, (app_callback_data,))
    db.exit_db()

    if app_data:
        app_id, name_app, link, is_available, code_text = app_data
        status = 'активно' if is_available else 'не активно'

        photo_file = os.path.join(IMAGE_FOLDER, f"app_{app_id}.jpg")
        video_file = os.path.join(IMAGE_FOLDER, f"app_{app_id}.mp4")

        photo_exists = os.path.isfile(photo_file)
        video_exists = os.path.isfile(video_file)

        edit_keyboard = edit_keyboard_admin(app_id)
        text = f"Редактирование {name_app} - {status}\nСсылка: {link}"

        text = (f"{name_app} - {status}\nСсылка: {link}\n"
                f"Code Text: {code_text}\n"
                f"Фото: {'есть' if photo_exists else 'отсутствует'}\n"
                f"Видео: {'есть' if video_exists else 'отсутствует'}")

    else:
        edit_keyboard = None
        text = "Приложение не найдено."

    return text, edit_keyboard


def load_text_app_admin_id(app_id):
    db = DBClient()

    query_select = 'SELECT id, name_app, link, is_available, code_text FROM apps WHERE id = %s'
    app_data = db.select_fetchone(query_select, (app_id,))
    db.exit_db()

    if app_data:
        app_id, name_app, link, is_available, code_text = app_data
        status = 'активно' if is_available else 'не активно'

        photo_file = os.path.join(IMAGE_FOLDER, f"app_{app_id}.jpg")
        video_file = os.path.join(IMAGE_FOLDER, f"app_{app_id}.mp4")

        photo_exists = os.path.isfile(photo_file)
        video_exists = os.path.isfile(video_file)

        edit_keyboard = edit_keyboard_admin(app_id)
        # text = f"Редактирование {name_app} - {status}\nСсылка: {link}"

        text = (f"{name_app} - {status}\nСсылка: {link}\n"
                f"Code Text: {code_text}\n"
                f"Фото: {'есть' if photo_exists else 'отсутствует'}\n"
                f"Видео: {'есть' if video_exists else 'отсутствует'}")

    else:
        edit_keyboard = None
        text = "Приложение не найдено."

    return text, edit_keyboard


def edit_keyboard_admin(app_id):
    edit_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить статус", callback_data=f"change_status_{app_id}")],
        [InlineKeyboardButton(text="Изменить название", callback_data=f"change_name_{app_id}")],
        [InlineKeyboardButton(text="Изменить ссылку", callback_data=f"change_link_{app_id}")],
        [InlineKeyboardButton(text="Изменить Код Текстовый", callback_data=f"change_text_{app_id}")],
        [InlineKeyboardButton(text="Изменить Код Видео", callback_data=f"change_video_{app_id}")],
        [InlineKeyboardButton(text="Изменить изображение", callback_data=f"change_image_{app_id}")],
        [InlineKeyboardButton(text="ТЕСТОВАЯ РАССЫЛКА (ВСЕ СЕБЕ)", callback_data=f"mail_me_{app_id}")],
        [InlineKeyboardButton(text="Запустить рассылку Текст", callback_data=f"mail_text_{app_id}")],
        [InlineKeyboardButton(text="Запустить рассылку Видео", callback_data=f"mail_video_{app_id}")],
        [InlineKeyboardButton(text="Запустить рассылку Картинка", callback_data=f"mail_image_{app_id}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"admin_panel")],
    ])

    return edit_keyboard


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
