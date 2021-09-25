import os
import json
import time
import asyncio

from asyncio.exceptions import TimeoutError

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired
)


API_ID = """
╭━━━━━━━━━━╮\n"
╭╮╱╱╱╱╭╮╭╮
┃┃╱╱╱╱┃┃┃┃
┃╰━┳━━┫┃┃┃╭━━╮
┃╭╮┃╭╮┃┃┃┃┃╭╮┃
┃┃┃┃╭╮┃╰┫╰┫╰╯┃
╰╯╰┻╯╰┻━┻━┻━━╯ {},
╰━━━━━━━━━━╯\n"
Buat string Session disini.

Masukan `API_ID`  Disini
║▌│█║▌│ █║▌│█│║▌║
"""
IP_HASH = "Disini `API_HASH` ║▌│█║▌│ █║▌│█│║▌.\n\nTap /cancel untuk Cancel.

PHONE_NUMBER_TEXT = (
    "📞__ Masukan nomor telephon"
    "Wajib dengan kode Negara.__\n**Contoh:** `+13124562345`\n\n"
    "Press /cancel untuk Cancel."
)



@Client.on_message(filters.private & filters.command("start"))
async def generate_str(c, m):
    get_api_id = await c.ask(
        chat_id=m.chat.id,
        text=API_TEXT.format(m.from_user.mention(style='md')),
        filters=filters.text
    )
    api_id = get_api_id.text
    if await is_cancel(m, api_id):
        return

    await get_api_id.delete()
    await get_api_id.request.delete()
    try:
        check_api = int(api_id)
    except Exception:
        await m.reply("**--🛑 API ID Invalid 🛑--**\nTap /start untuk buat ulang.")
        return

    get_api_hash = await c.ask(
        chat_id=m.chat.id, 
        text=HASH_TEXT,
        filters=filters.text
    )
    api_hash = get_api_hash.text
    if await is_cancel(m, api_hash):
        return

    await get_api_hash.delete()
    await get_api_hash.request.delete()

    if not len(api_hash) >= 30:
        await m.reply("--**🛑 API HASH Invalid 🛑**--\nTap /start untuk membuat ulang.")
        return

    try:
        client = Client(":memory:", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await c.send_message(m.chat.id ,f"**🛑 ERROR: 🛑** `{str(e)}`\nTap /start untuk membuat ulang.")
        return

    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    while True:
        get_phone_number = await c.ask(
            chat_id=m.chat.id,
            text=PHONE_NUMBER_TEXT
        )
        phone_number = get_phone_number.text
        if await is_cancel(m, phone_number):
            return
        await get_phone_number.delete()
        await get_phone_number.request.delete()

        confirm = await c.ask(
            chat_id=m.chat.id,
            text=f'🔛 `{phone_number}` Jika sudah benar? (y/n): \n\ntype: `y` (Jika yes)\ntype: `n` (Jika no)'
        )
        if await is_cancel(m, confirm.text):
            return
        if "y" in confirm.text.lower():
            await confirm.delete()
            await confirm.request.delete()
            break
    try:
        code = await client.send_code(phone_number)
        await asyncio.sleep(1)
    except FloodWait as e:
        await m.reply(f"__Maaf untuk mengatakan bahwa Anda memiliki waktu tunggu {e.x} Detik__")
        return
    except ApiIdInvalid:
        await m.reply("API_ID atau API_HASH Tidak Valid.\n\nTekan /mulai untuk membuat lagi.")
        return
    except PhoneNumberInvalid:
        await m.reply("Nomor Telepon Anda Tidak Valid.`\n\nTekan /mulai untuk membuat lagi.")
        return

    try:
        sent_type = {"app": "Telegram App 💌",
            "sms": "SMS 💬",
            "call": "Phone call 📱",
            "flash_call": "phone flash call 📲"
        }[code.type]
        otp = await c.ask(
            chat_id=m.chat.id,
            text=(f"Saya telah mengirim OTP ke nomor `{phone_number}` melalui {sent_type}\n\n"
                  "Silakan masukkan OTP dalam format `1 2 3 4 5` __(berikan spasi di antara angka)__\n\n"
                  "Jika Bot tidak mengirim OTP maka coba / mulai Bot.\n"
                  "Press /cancel untuk Cancel."), timeout=300)
    except TimeoutError:
        await m.reply("**TimeOut Error:** Anda mencapai batas waktu 5 menit.\nTap /mulai untuk membuat lagi.")
        return
    if await is_cancel(m, otp.text):
        return
    otp_code = otp.text
    await otp.delete()
    await otp.request.delete()
    try:
        await client.sign_in(phone_number, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await m.reply("**Kode Tidak Valid**\n\nTap /mulai untuk membuat lagi.")
        return 
    except PhoneCodeExpired:
        await m.reply("**Kode Kedaluwarsa**\n\nTap /mulai untuk membuat lagi.")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await c.ask(
                chat_id=m.chat.id, 
                text="`🔐 Akun ini memiliki kode verifikasi dua langkah.\Silakan masukkan kode otentikasi faktor kedua Anda.`\Tap /batal untuk Membatalkan.",
                timeout=300
            )
        except TimeoutError:
            await m.reply("**Kesalahan Waktu Habis:** Anda mencapai batas Waktu 5 mnt.\nTap /mulai untuk membuat lagi.")
            return
        if await is_cancel(m, two_step_code.text):
            return
        new_code = two_step_code.text
        await two_step_code.delete()
        await two_step_code.request.delete()
        try:
            await client.check_password(new_code)
        except Exception as e:
            await m.reply(f"**⚠️ ERROR:** `{str(e)}`")
            return
    except Exception as e:
        await c.send_message(m.chat.id ,f"**⚠️ ERROR:** `{str(e)}`")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"**Sesi String Anda **\n\n`{session_string}`\n\nTerima kasih Telah menggunakan {(menunggu c.get_me()).mention(style='md')}")
        text = "✅ Berhasil Membuat Sesi String Anda dan mengirimkan kepada Anda pesan tersimpan.\nPeriksa pesan tersimpan Anda atau Klik Tombol Di Bawah."
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="String Session ↗️", url=f"tg://openmessage?user_id={m.chat.id}")]]
        )
        await c.send_message(m.chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await c.send_message(m.chat.id ,f"**⚠️ ERROR:** `{str(e)}`")
        return
    try:
        await client.stop()
    except:
        pass


@Client.on_message(filters.private & filters.command("help"))
async def help(c, m):
    await help_cb(c, m, cb=False)


@Client.on_callback_query(filters.regex('^help$'))
async def help_cb(c, m, cb=True):
    help_text = """Superman datang menolong**


➺ Tekan tombol mulai

➺ Kirim API_ID Anda saat bot bertanya.

➺ Kemudian kirim API_HASH Anda saat bot memintanya.

➺ Kirim nomor ponsel Anda.

➺ Kirim OTP yang diterima ke nomor Anda dalam format `1 2 3 4 5` (Beri spasi b/w setiap digit)

➺ (Jika Anda memiliki verifikasi dua langkah, kirim ke bot jika bot bertanya.)


**CATATAN:**

Jika Anda membuat kesalahan di mana saja, tekan /batal lalu tekan /mulai
"""

    buttons = [[
        InlineKeyboardButton('📕 About', callback_data='about'),
        InlineKeyboardButton('❌ Close', callback_data='close')
    ]]
    if cb:
        await m.answer()
        await m.message.edit(text=help_text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
    else:
        await m.reply_text(text=help_text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True, quote=True)


@Client.on_message(filters.private & filters.command("about"))
async def about(c, m):
    await about_cb(c, m, cb=False)


@Client.on_callback_query(filters.regex('^about$'))
async def about_cb(c, m, cb=True):
    me = await c.get_me()
    about_text = f"""**ME:**

__🤖 My Name:__ {me.mention(style='md')}
    
__📝 Language:__ [Python3](https://www.python.org/)

__🧰 Framework:__ [Pyrogram](https://github.com/pyrogram/pyrogram)

__👨‍💻 Modification:__ [𝐀𝐧𝐨𝐧𝐲𝐦𝐨𝐮𝐬](https://t.me/bcddgblg)
"""

    buttons = [[
        InlineKeyboardButton('💡 Help', callback_data='help'),
        InlineKeyboardButton('❌ Close', callback_data='close')
    ]]
    if cb:
        await m.answer()
        await m.message.edit(about_text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
    else:
        await m.reply_text(about_text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True, quote=True)


@Client.on_callback_query(filters.regex('^close$'))
async def close(c, m):
    await m.message.delete()
    await m.message.reply_to_message.delete()


async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("⛔ Process Cancelled.")
        return True
    return False


