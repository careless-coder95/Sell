import asyncio
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode
from utils.keyboards import kb_back_main
from utils.state import set_state, get_state, update_data, clear_state
from database.db import count_accounts

ORDINALS = [
    "First", "Second", "Third", "Fourth", "Fifth",
    "Sixth", "Seventh", "Eighth", "Ninth", "Tenth",
    "11th", "12th", "13th", "14th", "15th",
    "16th", "17th", "18th", "19th", "20th",
]

def get_ordinal(n: int) -> str:
    if n <= len(ORDINALS):
        return ORDINALS[n - 1]
    return f"{n}th"


async def cb_start_love(client: Client, callback: CallbackQuery):
    uid = callback.from_user.id
    acc_count = count_accounts(uid)

    if acc_count == 0:
        await callback.answer("❌ Pehle koi account add karo!", show_alert=True)
        return

    clear_state(uid)
    set_state(uid, "awaiting_love_reason")

    await callback.message.edit_text(
        "<blockquote>❤️ <u>𝗦𝗧𝗔𝗥𝗧 𝗟𝗢𝗩𝗘</u></blockquote>\n\n"
        "<blockquote><b>➤ Love ka reason kya hai?</b>\n"
        "<b>Examples: <code>Propose</code>, <code>Hate</code>, <code>Marry</code></b></blockquote>\n\n"
        "<b>❌ Cancel: /cancel</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb_back_main()
    )


async def handle_love_flow(client: Client, message: Message):
    uid = message.from_user.id
    state = get_state(uid)
    if not state:
        return

    step = state["step"]
    data = state["data"]
    text = message.text.strip()

    # ── Step 1: Reason ───────────────────────────────────────
    if step == "awaiting_love_reason":
        update_data(uid, "reason", text)
        set_state(uid, "awaiting_love_count", data={"reason": text})

        await message.reply(
            f"<blockquote>✅ <b>Reason accepted: <code>{text}</code></b></blockquote>\n\n"
            "<blockquote>❤️ <u>𝗛𝗢𝗪 𝗠𝗔𝗡𝗬 𝗧𝗜𝗠𝗘𝗦?</u></blockquote>\n\n"
            "<blockquote><b>➤ Ek number enter karo (jaise: <code>6</code>)</b></blockquote>\n\n"
            "<b>❌ Cancel: /cancel</b>",
            parse_mode=ParseMode.HTML
        )

    # ── Step 2: Count ────────────────────────────────────────
    elif step == "awaiting_love_count":
        if not text.isdigit() or int(text) <= 0:
            await message.reply(
                "<b>⚠️ Sirf positive number enter karo. Jaise: <code>5</code></b>",
                parse_mode=ParseMode.HTML
            )
            return

        count = int(text)
        reason = data.get("reason", "Love")
        acc_count = count_accounts(uid)
        clear_state(uid)

        status_msg = await message.reply(
            f"<blockquote>❤️ <u>𝗟𝗢𝗩𝗘 𝗦𝗧𝗔𝗥𝗧𝗜𝗡𝗚...</u></blockquote>\n\n"
            f"<blockquote><b>💬 Reason: <code>{reason}</code></b>\n"
            f"<b>🔢 Count: <code>{count}</code></b>\n"
            f"<b>📱 Accounts: <code>{acc_count}</code></b></blockquote>\n\n"
            "─────────────────────",
            parse_mode=ParseMode.HTML
        )

        love_lines = []
        for i in range(1, count + 1):
            ordinal = get_ordinal(i)
            line = f"<b>{ordinal} love with {acc_count} account ❤️</b>"
            love_lines.append(line)

            display = "\n".join(love_lines)
            try:
                await status_msg.edit_text(
                    f"<blockquote>❤️ <u>𝗟𝗢𝗩𝗘 𝗜𝗡 𝗣𝗥𝗢𝗚𝗥𝗘𝗦𝗦...</u></blockquote>\n\n"
                    f"<blockquote><b>💬 Reason: <code>{reason}</code></b></blockquote>\n\n"
                    f"{display}",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass

            await asyncio.sleep(1)

        final_text = "\n".join(love_lines)
        await status_msg.edit_text(
            f"<blockquote>❤️ <u>𝗟𝗢𝗩𝗘 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘!</u></blockquote>\n\n"
            f"<blockquote><b>💬 Reason: <code>{reason}</code></b></blockquote>\n\n"
            f"{final_text}\n\n"
            "─────────────────────\n"
            "<b>☠️ Loving complete wait for upto 1hr to see your response</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_back_main()
  )
