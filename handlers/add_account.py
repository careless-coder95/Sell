import asyncio
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid, FloodWait
)
from utils.keyboards import kb_after_add, kb_main_menu, kb_back_main
from utils.state import set_state, get_state, update_data, clear_state
from database.db import save_account
import os

_login_clients: dict = {}


async def cb_add_account(client: Client, callback: CallbackQuery):
    uid = callback.from_user.id
    clear_state(uid)
    set_state(uid, "awaiting_phone")
    await callback.message.edit_text(
        "<blockquote>📱 <u>𝗔𝗗𝗗 𝗔𝗖𝗖𝗢𝗨𝗡𝗧</u></blockquote>\n\n"
        "<blockquote><b>➤ Phone number enter karo country code ke saath:</b>\n"
        "<b>Example: <code>+919XXXXXXXXX</code></b></blockquote>\n\n"
        "<b>❌ Cancel: /cancel</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb_back_main()
    )


async def handle_add_account_flow(client: Client, message: Message):
    uid = message.from_user.id
    state = get_state(uid)
    if not state:
        return

    step = state["step"]
    data = state["data"]
    text = message.text.strip()

    # ── Step 1: Phone ────────────────────────────────────────
    if step == "awaiting_phone":
        if not text.startswith("+"):
            await message.reply(
                "<b>⚠️ Phone number <code>+</code> se shuru hona chahiye.</b>\n"
                "<b>Example: <code>+919XXXXXXXXX</code></b>",
                parse_mode=ParseMode.HTML
            )
            return

        await message.reply(
            "<b>⏳ OTP bhej raha hoon...</b>",
            parse_mode=ParseMode.HTML
        )

        api_id = int(os.getenv("API_ID"))
        api_hash = os.getenv("API_HASH")

        temp_client = Client(
            f"temp_{uid}",
            api_id=api_id,
            api_hash=api_hash,
            in_memory=True
        )

        try:
            await temp_client.connect()
            sent = await temp_client.send_code(text)
            _login_clients[uid] = temp_client
            set_state(uid, "awaiting_otp", data={
                "phone": text,
                "phone_code_hash": sent.phone_code_hash
            })
            await message.reply(
                "<blockquote>🔐 <u>𝗢𝗧𝗣 𝗘𝗡𝗧𝗘𝗥 𝗞𝗔𝗥𝗢</u></blockquote>\n\n"
                "<blockquote><b>➤ Tumhare Telegram pe OTP aaya hai.</b>\n"
                "<b>➤ Woh yahan type karo:</b></blockquote>\n\n"
                "<b>❌ Cancel: /cancel</b>",
                parse_mode=ParseMode.HTML
            )
        except PhoneNumberInvalid:
            await temp_client.disconnect()
            await message.reply("<b>❌ Invalid phone number. Dobara try karo.</b>", parse_mode=ParseMode.HTML)
            clear_state(uid)
        except FloodWait as e:
            await temp_client.disconnect()
            await message.reply(f"<b>⏳ Flood wait: {e.value} seconds baad try karo.</b>", parse_mode=ParseMode.HTML)
            clear_state(uid)
        except Exception as e:
            await temp_client.disconnect()
            await message.reply(f"<b>❌ Error: <code>{e}</code></b>", parse_mode=ParseMode.HTML)
            clear_state(uid)

    # ── Step 2: OTP ──────────────────────────────────────────
    elif step == "awaiting_otp":
        temp_client = _login_clients.get(uid)
        if not temp_client:
            await message.reply("<b>❌ Session expired. Dobara /start karo.</b>", parse_mode=ParseMode.HTML)
            clear_state(uid)
            return

        otp = text.replace(" ", "")
        phone = data["phone"]
        phone_code_hash = data["phone_code_hash"]

        try:
            await temp_client.sign_in(phone, phone_code_hash, otp)
            await _finish_login(client, message, uid, temp_client, phone, "")
        except SessionPasswordNeeded:
            set_state(uid, "awaiting_2fa", data={
                "phone": phone,
                "phone_code_hash": phone_code_hash
            })
            await message.reply(
                "<blockquote>🔑 <u>𝟮𝗙𝗔 𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗</u></blockquote>\n\n"
                "<blockquote><b>➤ Tumhare account pe 2-step verification hai.</b>\n"
                "<b>➤ Password type karo:</b></blockquote>\n\n"
                "<b>❌ Cancel: /cancel</b>",
                parse_mode=ParseMode.HTML
            )
        except PhoneCodeInvalid:
            await message.reply("<b>❌ Galat OTP. Dobara try karo.</b>", parse_mode=ParseMode.HTML)
        except PhoneCodeExpired:
            await message.reply("<b>❌ OTP expire ho gaya. /start se dobara shuru karo.</b>", parse_mode=ParseMode.HTML)
            await temp_client.disconnect()
            _login_clients.pop(uid, None)
            clear_state(uid)
        except Exception as e:
            await message.reply(f"<b>❌ Error: <code>{e}</code></b>", parse_mode=ParseMode.HTML)

    # ── Step 3: 2FA ──────────────────────────────────────────
    elif step == "awaiting_2fa":
        temp_client = _login_clients.get(uid)
        if not temp_client:
            await message.reply("<b>❌ Session expired. Dobara /start karo.</b>", parse_mode=ParseMode.HTML)
            clear_state(uid)
            return

        phone = data["phone"]
        password = text

        try:
            await temp_client.check_password(password)
            await _finish_login(client, message, uid, temp_client, phone, password)
        except PasswordHashInvalid:
            await message.reply("<b>❌ Galat password. Dobara try karo.</b>", parse_mode=ParseMode.HTML)
        except Exception as e:
            await message.reply(f"<b>❌ Error: <code>{e}</code></b>", parse_mode=ParseMode.HTML)


async def _finish_login(
    bot: Client, message: Message,
    uid: int, temp_client: Client,
    phone: str, password: str
):
    try:
        session_string = await temp_client.export_session_string()
        await temp_client.disconnect()
        _login_clients.pop(uid, None)

        save_account(uid, phone, session_string, password)
        clear_state(uid)

        await message.reply(
            "<blockquote>✅ <u>𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗦𝗔𝗩𝗘𝗗!</u></blockquote>\n\n"
            f"<blockquote><b>📱 Number: <code>{phone}</code></b>\n"
            "<b>🔒 Session securely stored locally.</b></blockquote>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_after_add()
        )
    except Exception as e:
        await message.reply(f"<b>❌ Session save karne mein error: <code>{e}</code></b>", parse_mode=ParseMode.HTML)
        clear_state(uid)
