from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from utils.state import clear_state
from utils.keyboards import kb_main_menu


async def cmd_cancel(client: Client, message: Message):
    uid = message.from_user.id
    clear_state(uid)
    await message.reply(
        "<blockquote>❌ <u>𝗖𝗔𝗡𝗖𝗘𝗟𝗟𝗘𝗗</u></blockquote>\n"
        "<blockquote><b>➤ Came back to the main menu.</b></blockquote>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb_main_menu(uid)
    )
