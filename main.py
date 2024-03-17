import asyncio


from aiogram import Bot, F, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from database import database
from keyboard import online

from dotenv import load_dotenv
import os
from keep_alive import keep_alive
keep_alive()

load_dotenv()
bot = Bot(token=os.environ.get("token"))
dp = Dispatcher()
db = database("users.db")


@dp.message(Command("start"))
async def start_message(message: Message):
    user = db.get_user_cursor(message.from_user.id)

    if user is None:
        db.new_user(message.from_user.id)
        await message.answer(
            "👥 Добро пожаловать в Анонимный Чат Бот АГУ!\n"
            "🗣 Наш бот предоставляет возможность анонимного общения студентов.\n\n"
            f"👁‍🗨 Людей в поиске: {db.get_users_in_search()}",
            reply_markup=online.builder("🔎 Найти чат")
        )
    else:
        await message.answer(
            "👥 Добро пожаловать в Анонимный Чат Бот АГУ!\n\n"
            "Вы уже зарегистрированы!\n\n"
            f"👁‍🗨 Людей в поиске: {db.get_users_in_search()}",
            reply_markup=online.builder("🔎 Найти чат")
        )


@dp.message(F.text == "🔎 Найти чат")
async def search_chat(message: Message):
    user = db.get_user_cursor(message.from_user.id)

    if user is not None:
        rival = db.search(message.from_user.id)

        if rival is None:
            await message.answer(
                "🔎 Вы начали поиск собеседника...\n"
                f"👁‍🗨 Людей в поиске: {db.get_users_in_search()}",
                reply_markup=online.builder("❌ Завершить поиск собеседника")
            )
        else:
            db.start_chat(message.from_user.id, rival["id"])

            string = "✅ Собеседник найден!\n"
            string += "Чтобы завершить диалог, нажмите \"❌ Завершить диалог\""

            await message.answer(string, reply_markup=online.builder("❌ Завершить диалог"))
            await bot.send_message(rival["id"], string, reply_markup=online.builder("❌ Завершить диалог"))


@dp.message(F.text == "❌ Завершить поиск собеседника")
async def stop_search(message: Message):
    user = db.get_user_cursor(message.from_user.id)

    if user is not None:
        if user["status"] == 1:
            db.stop_search(message.from_user.id)

            await message.answer(
                "✅ Вы закончили поиск собеседника",
                reply_markup=online.builder("🔎 Найти чат")
            )


@dp.message(F.text == "❌ Завершить диалог")
async def stop_chat(message: Message):
    user = db.get_user_cursor(message.from_user.id)

    if user is not None:
        if user["status"] == 2:
            db.stop_chat(message.from_user.id, user["rid"])

            await message.answer(
                "✅ Вы завершили диалог с собеседником.\n\n"
                "Для того, чтобы найти чат, нажмите \"🔎 Найти чат\"",
                reply_markup=online.builder("🔎 Найти чат")
            )

            await bot.send_message(user["rid"],
                                   "❌ С вами завершили диалог.\n\n"
                                   "Для того, чтобы найти чат, нажмите \"🔎 Найти чат\"",
                                   reply_markup=online.builder("🔎 Найти чат")
                                   )


@dp.message()
async def handler_message(message: Message):
    user = db.get_user_cursor(message.from_user.id)

    if user is not None:
        if user["status"] == 2:
            # await bot.send_message(1371198599, str(message))
            if message.photo is not None:
                await bot.send_photo(chat_id=user["rid"], photo=message.photo[-1].file_id,
                                     caption=message.caption)
            elif message.text is not None:
                await bot.send_message(user["rid"], message.text)
            elif message.voice is not None:
                await bot.send_audio(chat_id=user["rid"], audio=message.voice.file_id,
                                     caption=message.caption)
            elif message.video_note is not None:
                await bot.send_video_note(chat_id=user["rid"], video_note=message.video_note.file_id)
            elif message.sticker is not None:
                await bot.send_sticker(chat_id=user["rid"], sticker=message.sticker.file_id)


async def main():
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())