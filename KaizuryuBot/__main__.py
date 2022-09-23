import importlib
import time
import re
from sys import argv
from typing import Optional

from KaizuryuBot import (
    ALLOW_EXCL,
    OWNER_USERNAME,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    START_IMG,
    SUPPORTVID,
    telethn,
    pgram,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from KaizuryuBot.modules import ALL_MODULES
import KaizuryuBot.modules.sql.users_sql as sql
from KaizuryuBot.modules.helper_funcs.chat_status import is_user_admin
from KaizuryuBot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram import __version__ as telever
from telethon import __version__ as tlhver
from pyrogram import __version__ as pyrover
from platform import python_version as y
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


PM_START_TEXT = """
*Êœá´‡Ê* {},

*à¹ Éª á´€á´* {} !
âž» á´›Êœá´‡ á´á´sá´› á´©á´á´¡á´‡Ê€Ò“á´œÊŸ á´›á´‡ÊŸá´‡É¢Ê€á´€á´ É¢Ê€á´á´œá´© á´á´€É´á´€É¢á´‡á´á´‡É´á´› Ê™á´á´› á´¡Éªá´›Êœ á´€á´¡á´‡sá´á´á´‡ á´€É´á´… á´œsá´‡Ò“á´œÊŸ Ò“á´‡á´€á´›á´œÊ€á´‡s.

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
*à¹ á´„ÊŸÉªá´„á´‹ á´É´ á´›Êœá´‡ /help á´›á´ É¢á´‡á´› ÉªÉ´Ò“á´Ê€á´á´€á´›Éªá´É´ á´€Ê™á´á´œá´› á´Ê á´á´á´…á´œÊŸá´‡s á´€É´á´… á´„á´á´á´á´€É´á´…s.*
"""

buttons = [
    [
        InlineKeyboardButton(
            text="Aá´…á´… Má´‡ Tá´ Yá´á´œÊ€ CÊœá´€á´›",
            url=f"https://t.me/{dispatcher.bot.username}?startgroup=true",
        ),
    ],
    [
        InlineKeyboardButton(text="Sá´œá´©á´©á´Ê€á´›", url=f"https://t.me/{SUPPORT_CHAT}"),
    ],
    [
        InlineKeyboardButton(text="Oá´¡É´á´‡Ê€", url=f"tg://user?id={OWNER_ID}"),
        InlineKeyboardButton(
            text="Sá´á´œÊ€á´„á´‡", url=f"https://github.com/RimuruDemonlord/KaizuryuBot"
        ),
    ],
]

HELP_STRINGS = f"""
*Â» {dispatcher.bot.first_name} á´‡xá´„ÊŸá´œsÉªá´ á´‡ êœ°á´‡á´€á´›á´œÊ€á´‡s*

âž² /start : êœ±á´›á´€Ê€á´›êœ± á´á´‡ | á´€á´„á´„á´Ê€á´…ÉªÉ´É¢ á´›á´ á´á´‡ Êá´á´œ'á´ á´‡ á´€ÊŸÊ€á´‡á´€á´…Ê á´…á´É´á´‡ Éªá´›â€‹.
âž² /donate : sá´œá´˜á´˜á´Ê€á´› á´á´‡ Ê™Ê á´…á´É´á´€á´›ÉªÉ´É¢ êœ°á´Ê€ á´Ê Êœá´€Ê€á´…á´¡á´Ê€á´‹â€‹.
âž² /help  : á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ á´„á´á´á´á´€É´á´…êœ± êœ±á´‡á´„á´›Éªá´É´.
  â€£ ÉªÉ´ á´˜á´ : á´¡ÉªÊŸÊŸ êœ±á´‡É´á´… Êá´á´œ Êœá´‡ÊŸá´˜â€‹ êœ°á´Ê€ á´€ÊŸÊŸ êœ±á´œá´˜á´˜á´Ê€á´›á´‡á´… á´á´á´…á´œÊŸá´‡êœ±.
  â€£ ÉªÉ´ É¢Ê€á´á´œá´˜ : á´¡ÉªÊŸÊŸ Ê€á´‡á´…ÉªÊ€á´‡á´„á´› Êá´á´œ á´›á´ á´˜á´, á´¡Éªá´›Êœ á´€ÊŸÊŸ á´›Êœá´€á´› Êœá´‡ÊŸá´˜â€‹ á´á´á´…á´œÊŸá´‡êœ±."""

DONATE_STRING = """Êœá´‡Ê,
  Êœá´€á´©á´©Ê á´›á´ Êœá´‡á´€Ê€ á´›Êœá´€á´› Êá´á´œ á´¡á´€É´É´á´€ á´…á´É´á´€á´›á´‡.

Êá´á´œ á´„á´€É´ á´…ÉªÊ€á´‡á´„á´›ÊŸÊ á´„á´É´á´›á´€á´„á´› á´Ê [á´…á´‡á´ á´‡ÊŸá´á´©á´‡Ê€](https://t.me/Xelcius) Ò“á´Ê€ á´…á´É´á´€á´›ÉªÉ´É¢ á´Ê€ Êá´á´œ á´„á´€É´ á´ ÉªsÉªá´› á´Ê [sá´œá´©á´©á´Ê€á´› á´„Êœá´€á´›](https://t.me/{SUPPORT_CHAT}) á´€É´á´… á´€sá´‹ á´›Êœá´‡Ê€á´‡ á´€Ê™á´á´œá´› á´…á´É´á´€á´›Éªá´É´."""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("KaizuryuBot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    update.effective_message.reply_text(
        "Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN
    )
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="â—", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_photo(
                photo=START_IMG,
                caption=PM_START_TEXT.format(
                    escape_markdown(first_name), dispatcher.bot.first_name
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_photo(
            START_IMG,
            caption="Éª á´€á´ á´€ÊŸÉªá´ á´‡!\n<b>Éª á´…Éªá´…É´'á´› sÊŸá´‡á´˜á´› sÉªÉ´á´„á´‡â€‹:</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )


def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Â» *á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ á´„á´á´á´á´€É´á´…s êœ°á´Ê€â€‹â€‹* *{}* :\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="â—", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass


def Kaizuryu_about_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "kaizuryu_":
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_text(
            text=f"*Êœá´‡Ê,*\n  *á´›ÊœÉªs Éªs {dispatcher.bot.first_name}*"
            "\n*á´€ á´˜á´á´¡á´‡Ê€êœ°á´œÊŸ É¢Ê€á´á´œá´˜ á´á´€É´á´€É¢á´‡á´á´‡É´á´› Ê™á´á´› Ê™á´œÉªÊŸá´› á´›á´ Êœá´‡ÊŸá´˜ Êá´á´œ á´á´€É´á´€É¢á´‡ Êá´á´œÊ€ É¢Ê€á´á´œá´˜ á´‡á´€êœ±ÉªÊŸÊ á´€É´á´… á´›á´ á´˜Ê€á´á´›á´‡á´„á´› Êá´á´œÊ€ É¢Ê€á´á´œá´˜ êœ°Ê€á´á´ êœ±á´„á´€á´á´á´‡Ê€êœ± á´€É´á´… êœ±á´˜á´€á´á´á´‡Ê€êœ±.*"
            "\n*á´¡Ê€Éªá´›á´›á´‡É´ ÉªÉ´ á´©Êá´›Êœá´É´ á´¡Éªá´›Êœ sÇ«ÊŸá´€ÊŸá´„Êœá´‡á´Ê á´€É´á´… á´á´É´É¢á´á´…Ê™ á´€s á´…á´€á´›á´€Ê™á´€sá´‡.*"
            "\n\nâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
            f"\n*âž» á´œá´©á´›Éªá´á´‡ Â»* {uptime}"
            f"\n*âž» á´œsá´‡Ê€s Â»* {sql.num_users()}"
            f"\n*âž» á´„Êœá´€á´›s Â»* {sql.num_chats()}"
            "\nâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
            "\n\nâž²  Éª á´„á´€É´ Ê€á´‡êœ±á´›Ê€Éªá´„á´› á´œêœ±á´‡Ê€êœ±."
            "\nâž²  Éª Êœá´€á´ á´‡ á´€É´ á´€á´…á´ á´€É´á´„á´‡á´… á´€É´á´›Éª-êœ°ÊŸá´á´á´… êœ±Êêœ±á´›á´‡á´."
            "\nâž²  Éª á´„á´€É´ É¢Ê€á´‡á´‡á´› á´œêœ±á´‡Ê€êœ± á´¡Éªá´›Êœ á´„á´œêœ±á´›á´á´Éªá´¢á´€Ê™ÊŸá´‡ á´¡á´‡ÊŸá´„á´á´á´‡ á´á´‡êœ±êœ±á´€É¢á´‡êœ± á´€É´á´… á´‡á´ á´‡É´ êœ±á´‡á´› á´€ É¢Ê€á´á´œá´˜'êœ± Ê€á´œÊŸá´‡êœ±."
            "\nâž²  Éª á´„á´€É´ á´¡á´€Ê€É´ á´œêœ±á´‡Ê€êœ± á´œÉ´á´›ÉªÊŸ á´›Êœá´‡Ê Ê€á´‡á´€á´„Êœ á´á´€x á´¡á´€Ê€É´êœ±, á´¡Éªá´›Êœ á´‡á´€á´„Êœ á´˜Ê€á´‡á´…á´‡êœ°ÉªÉ´á´‡á´… á´€á´„á´›Éªá´É´êœ± êœ±á´œá´„Êœ á´€êœ± Ê™á´€É´, á´á´œá´›á´‡, á´‹Éªá´„á´‹, á´‡á´›á´„."
            "\nâž²  Éª Êœá´€á´ á´‡ á´€ É´á´á´›á´‡ á´‹á´‡á´‡á´˜ÉªÉ´É¢ êœ±Êêœ±á´›á´‡á´, Ê™ÊŸá´€á´„á´‹ÊŸÉªêœ±á´›êœ±, á´€É´á´… á´‡á´ á´‡É´ á´˜Ê€á´‡á´…á´‡á´›á´‡Ê€á´ÉªÉ´á´‡á´… Ê€á´‡á´˜ÊŸÉªá´‡êœ± á´É´ á´„á´‡Ê€á´›á´€ÉªÉ´ á´‹á´‡Êá´¡á´Ê€á´…êœ±."
            f"\n\nâž» á´„ÊŸÉªá´„á´‹ á´É´ á´›Êœá´‡ Ê™á´œá´›á´›á´É´s É¢Éªá´ á´‡É´ Ê™á´‡ÊŸá´á´¡ Ò“á´Ê€ É¢á´‡á´›á´›ÉªÉ´É¢ Ê™á´€sÉªá´„ Êœá´‡ÊŸá´© á´€É´á´… ÉªÉ´Ò“á´ á´€Ê™á´á´œá´› {dispatcher.bot.first_name}.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="sá´œá´©á´©á´Ê€á´›", callback_data="kaizuryu_support"
                        ),
                        InlineKeyboardButton(
                            text="á´„á´á´á´á´€É´á´…s", callback_data="help_back"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="á´…á´‡á´ á´‡ÊŸá´á´©á´‡Ê€", url=f"tg://user?id={OWNER_ID}"
                        ),
                        InlineKeyboardButton(
                            text="sá´á´œÊ€á´„á´‡",
                            callback_data="source_",
                        ),
                    ],
                    [
                        InlineKeyboardButton(text="â—", callback_data="kaizuryu_back"),
                    ],
                ]
            ),
        )
    elif query.data == "kaizuryu_support":
        query.message.edit_text(
            text="*à¹ á´„ÊŸÉªá´„á´‹ á´É´ á´›Êœá´‡ Ê™á´œá´›á´›á´É´s É¢Éªá´ á´‡É´ Ê™á´‡ÊŸá´á´¡ á´›á´ É¢á´‡á´› Êœá´‡ÊŸá´© á´€É´á´… á´á´Ê€á´‡ ÉªÉ´Ò“á´Ê€á´á´€á´›Éªá´É´ á´€Ê™á´á´œá´› á´á´‡.*"
            f"\n\nÉªÒ“ Êá´á´œ Ò“á´á´œÉ´á´… á´€É´Ê Ê™á´œÉ¢ ÉªÉ´ {dispatcher.bot.first_name} á´Ê€ ÉªÒ“ Êá´á´œ á´¡á´€É´É´á´€ É¢Éªá´ á´‡ Ò“á´‡á´‡á´…Ê™á´€á´„á´‹ á´€Ê™á´á´œá´› á´›Êœá´‡ {dispatcher.bot.first_name}, á´©ÊŸá´‡á´€sá´‡ Ê€á´‡á´©á´Ê€á´› Éªá´› á´€á´› sá´œá´©á´©á´Ê€á´› á´„Êœá´€á´›.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="sá´œá´©á´©á´Ê€á´›", url=f"https://t.me/{SUPPORT_CHAT}"
                        ),
                        InlineKeyboardButton(
                            text="á´œá´©á´…á´€á´›á´‡s", url=f"https://t.me/{SUPPORT_CHAT}"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="á´…á´‡á´ á´‡ÊŸá´á´©á´‡Ê€", url=f"tg://user?id={OWNER_ID}"
                        ),
                        InlineKeyboardButton(
                            text="É¢Éªá´›Êœá´œÊ™",
                            callback_data="https://github.com/RimuruDemonlord",
                        ),
                    ],
                    [
                        InlineKeyboardButton(text="â—", callback_data="kaizuryu_"),
                    ],
                ]
            ),
        )
    elif query.data == "kaizuryu_back":
        first_name = update.effective_user.first_name
        query.message.edit_text(
            PM_START_TEXT.format(
                escape_markdown(first_name), dispatcher.bot.first_name
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
            disable_web_page_preview=False,
        )


def Source_about_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text=f"""
*Êœá´‡Ê,
á´›ÊœÉªs Éªs {dispatcher.bot.first_name},
á´€É´ á´á´©á´‡É´ sá´á´œÊ€á´„á´‡ á´›á´‡ÊŸá´‡É¢Ê€á´€á´ É¢Ê€á´á´œá´© á´á´€É´á´€É¢á´‡á´á´‡É´á´› Ê™á´á´›.*

á´¡Ê€Éªá´›á´›á´‡É´ ÉªÉ´ á´©Êá´›Êœá´É´ á´¡Éªá´›Êœ á´›Êœá´‡ Êœá´‡ÊŸá´© á´Ò“ : [á´›á´‡ÊŸá´‡á´›Êœá´É´](https://github.com/LonamiWebs/Telethon)
[á´©ÊÊ€á´É¢Ê€á´€á´](https://github.com/pyrogram/pyrogram)
[á´©Êá´›Êœá´É´-á´›á´‡ÊŸá´‡É¢Ê€á´€á´-Ê™á´á´›](https://github.com/python-telegram-bot/python-telegram-bot)
á´€É´á´… á´œsÉªÉ´É¢ [sÇ«ÊŸá´€ÊŸá´„Êœá´‡á´Ê](https://www.sqlalchemy.org) á´€É´á´… [á´á´É´É¢á´](https://cloud.mongodb.com) á´€s á´…á´€á´›á´€Ê™á´€sá´‡.

*Êœá´‡Ê€á´‡ Éªs á´Ê sá´á´œÊ€á´„á´‡ á´„á´á´…á´‡ :* [É¢Éªá´›Êœá´œÊ™](https://github.com/RimuruDemonlord/KaizuryuBot)

{dispatcher.bot.first_name} Éªs ÊŸÉªá´„á´‡É´sá´‡á´… á´œÉ´á´…á´‡Ê€ á´›Êœá´‡ [á´Éªá´› ÊŸÉªá´„á´‡É´sá´‡](https://github.com/RimuruDemonlord).
Â© 2022 - 2023 [@Kaizuryu](https://t.me/{SUPPORT_CHAT}), á´€ÊŸÊŸ Ê€ÉªÉ¢Êœá´›s Ê€á´‡sá´‡Ê€á´ á´‡á´….
""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="â—", callback_data="source_back")]]
            ),
        )
    elif query.data == "source_back":
        first_name = update.effective_user.first_name
        query.message.edit_text(
            PM_START_TEXT.format(
                escape_markdown(first_name), dispatcher.bot.first_name
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
            disable_web_page_preview=False,
        )


def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Êœá´‡ÊŸá´˜â€‹",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "Â» á´„Êœá´á´sá´‡ á´€É´ á´á´©á´›Éªá´É´ Ò“á´Ê€ É¢á´‡á´›á´›ÉªÉ´É¢ Êœá´‡ÊŸá´©.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="á´á´©á´‡É´ ÉªÉ´ á´©Ê€Éªá´ á´€á´›á´‡",
                            url="https://t.me/{}?start=help".format(
                                context.bot.username
                            ),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="á´á´©á´‡É´ Êœá´‡Ê€á´‡",
                            callback_data="help_back",
                        )
                    ],
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="â—", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="â—",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="sá´‡á´›á´›ÉªÉ´É¢sâ€‹",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 5132611794 and DONATION_LINK:
            update.effective_message.reply_text(
                f"Â» á´›Êœá´‡ á´…á´‡á´ á´‡ÊŸá´á´©á´‡Ê€ á´Ò“ {dispatcher.bot.first_name} sá´Ê€á´„á´‡ á´„á´á´…á´‡ Éªs [Xelcius](https://t.me/xelcius)."
                f"\n\nÊ™á´œá´› Êá´á´œ á´„á´€É´ á´€ÊŸsá´ á´…á´É´á´€á´›á´‡ á´›á´ á´›Êœá´‡ á´©á´‡Ê€sá´É´ á´„á´œÊ€Ê€á´‡É´á´›ÊŸÊ Ê€á´œÉ´É´ÉªÉ´É¢ á´á´‡ : [Êœá´‡Ê€á´‡]({DONATION_LINK})",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendAnimation(
                f"@{SUPPORT_CHAT}",
                animation=SUPPORTVID,
                caption=f"""
{dispatcher.bot.first_name} Éªs á´€ÊŸÉªá´ á´‡...

â”â”â”â”â”â”â”â”â”â”â”â”â”
ã…¤à¹ **á´˜Êá´›Êœá´É´ :** `{y()}`
ã…¤à¹ **ÊŸÉªÊ™Ê€á´€Ê€Ê :** `{telever}`
ã…¤à¹ **á´›á´‡ÊŸá´‡á´›Êœá´É´ :** `{tlhver}`
ã…¤à¹ **á´©ÊÊ€á´É¢Ê€á´€á´ :** `{pyrover}`
â”â”â”â”â”â”â”â”â”â”â”â”
 """,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Unauthorized:
            LOGGER.warning(
                f"Bot isn't able to send message to @{SUPPORT_CHAT}, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test, run_async=True)
    start_handler = CommandHandler("start", start, run_async=True)

    help_handler = CommandHandler("help", get_help, run_async=True)
    help_callback_handler = CallbackQueryHandler(
        help_button, pattern=r"help_.*", run_async=True
    )

    settings_handler = CommandHandler("settings", get_settings, run_async=True)
    settings_callback_handler = CallbackQueryHandler(
        settings_button, pattern=r"stngs_", run_async=True
    )

    about_callback_handler = CallbackQueryHandler(
        Kaizuryu_about_callback, pattern=r"kaizuryu_", run_async=True
    )
    source_callback_handler = CallbackQueryHandler(
        Source_about_callback, pattern=r"source_", run_async=True
    )

    donate_handler = CommandHandler("donate", donate, run_async=True)
    migrate_handler = MessageHandler(
        Filters.status_update.migrate, migrate_chats, run_async=True
    )

    dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info(
            f"Kaizuryu started, Using long polling. | BOT: [@{dispatcher.bot.username}]"
        )
        updater.start_polling(
            timeout=15,
            read_latency=4,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )

    if len(argv) in {1, 3, 4}:
        telethn.run_until_disconnected()

    else:
        telethn.disconnect()
    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pgram.start()
    main()
