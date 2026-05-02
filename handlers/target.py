from pyrogram import Client
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode
from utils.keyboards import kb_target_menu, kb_target_save, kb_back_main
from utils.state import set_state, get_state, update_data, clear_state
from database.db import save_target, get_target, delete_target


async def cb_target_menu(client: Client, callback: CallbackQuery):
    uid = callback.from_user.id
    target = get_target(uid)
    clear_state(uid)

    if target:
        text = (
            "<blockquote>🎯 <u>𝗖𝗨𝗥𝗥𝗘𝗡𝗧 𝗧𝗔𝗥𝗚𝗘𝗧</u></blockquote>\n"
            f"<blockquote><b>👤 Name: {target.get('name', 'N/A')}</b>\n"
            f"<b>🆔 User ID: <code>{target.get('id', 'N/A')}</code></b>\n"
            f"<b>🔗 Username: @{target.get('username', 'N/A')}</b></blockquote>\n"
            "<blockquote><b>⚠️ To set a new target, delete it first..</b></blockquote>"
        )
    else:
        text = (
            "<blockquote>🎯 <u>𝗧𝗔𝗥𝗚𝗘𝗧</u></blockquote>\n\n"
            "<blockquote><b>🚫 No target is set.</b>\n"
            "<b>➤ Set the target from the button below.</b></blockquote>"
        )

    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb_target_menu(bool(target))
    )


async def cb_set_target(client: Client, callback: CallbackQuery):
    uid = callback.from_user.id
    set_state(uid, "awaiting_target_input")
    await callback.message.edit_text(
        "<blockquote>🔍 <u>𝗧𝗔𝗥𝗚𝗘𝗧 𝗦𝗘𝗧 𝗞𝗔𝗥𝗢</u></blockquote>\n"
        "<blockquote><b>➤ By entering Username:</b>\n"
        "<b>Example: <code>@username</code></b></blockquote>\n\n"
        "<b>❌ Cancel: /cancel</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb_back_main()
    )


async def handle_target_flow(client: Client, message: Message):
    uid = message.from_user.id
    state = get_state(uid)
    if not state or state["step"] != "awaiting_target_input":
        return

    text = message.text.strip()

    try:
        user = await client.get_users(text)
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        info = {
            "name": full_name,
            "id": user.id,
            "username": user.username or "N/A"
        }
        update_data(uid, "target_info", info)
        set_state(uid, "confirm_target", data={"target_info": info})

        await message.reply(
            "<blockquote>👤 <u>𝗨𝗦𝗘𝗥 𝗙𝗢𝗨𝗡𝗗!</u></blockquote>\n"
            f"<blockquote><b>👤 Name: {full_name}</b>\n"
            f"<b>🆔 User ID: <code>{user.id}</code></b>\n"
            f"<b>🔗 Username: @{user.username or 'N/A'}</b></blockquote>\n"
            "<blockquote><b>➤ Do you want to save your target with this?</b></blockquote>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_target_save()
        )
    except Exception as e:
        await message.reply(
            f"<b>🚫 User nahi mila: <code>{e}</code></b>\n\n<b>Dobara try karo.</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_back_main()
        )


async def cb_save_target(client: Client, callback: CallbackQuery):
    uid = callback.from_user.id
    state = get_state(uid)

    if not state or "target_info" not in state.get("data", {}):
        await callback.answer("🚫 No data was found. Try again.", show_alert=True)
        return

    info = state["data"]["target_info"]
    save_target(uid, info)
    clear_state(uid)

    await callback.answer("✅ Target saved!", show_alert=True)
    await callback.message.edit_text(
        "<blockquote>✅ <u>𝗧𝗔𝗥𝗚𝗘𝗧 𝗦𝗔𝗩𝗘𝗗!</u></blockquote>\n"
        f"<blockquote><b>👤 Name: {info['name']}</b>\n"
        f"<b>🆔 User ID: <code>{info['id']}</code></b>\n"
        f"<b>🔗 Username: @{info['username']}</b></blockquote>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb_target_menu(True)
    )


async def cb_delete_target(client: Client, callback: CallbackQuery):
    uid = callback.from_user.id
    delete_target(uid)
    await callback.answer("🗑 Target deleted!", show_alert=True)
    await callback.message.edit_text(
        "<blockquote>🎯 <u>𝗧𝗔𝗥𝗚𝗘𝗧</u></blockquote>\n\n"
        "<blockquote><b>🚫 No target is set.</b>\n"
        "<b>➤ Set the target from the button below.</b></blockquote>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb_target_menu(False)
  )
