#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from daft_scrapper import DaftScrapper

TELEGRAM_TOKEN = "6030575142:AAGdVtYMGQTikYO9R_QTYokO_Lrt8GDIrW4"
CHECK_TIMEOUT = 300

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

async def alarm_cb(context: ContextTypes.DEFAULT_TYPE):
    """ Alarm callback."""
    # Constants & variables
    chat_id = context.job.chat_id
    price = context.job.data["price"]
    known_homes = context.job.data["known_homes"]
    # Check available homes
    home_list = DaftScrapper.daft_scrap(price)
    # Check if list is not empty
    if home_list is None:
        return
    # Send alarm if any home is new
    for home in home_list:
        if not any(known_home["id"] == home["id"] for known_home in known_homes):
            logger.info("New home: {home=}")
            known_homes.append(home)
            resp = f"⚠️ Alarm! New home available:\n"
            resp += f"{home['title']}\n"
            resp += f"{home['price']}\n"
            resp += f"{home['url']}"
            await context.bot.send_message(chat_id, resp)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    # Help message
    help_text = "¡Hola! Este bot busca casas de alquiler en daft.ie y te avisa si encuentra nuevas ofertas.\n"
    help_text += "Usa el comando /check <precio_maximo> para recibir las ofertas de casas de alquiler.\n"
    help_text += "Usa el comando /alarm <precio_maximo> para recibir alarmas de casas de alquiler.\n"
    help_text += "Usa el comando /stop para parar la alarma de casas de alquiler.\n"
    # Send help message
    await update.message.reply_text(help_text)

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    # Parse price
    if context.args:
        try:
            user_price = int(context.args[0])
        except:
            await update.message.reply_text(f"Invalid price: {user_args}")
    else:
        user_price = 1000
    # Check available homes
    home_list = DaftScrapper.daft_scrap(user_price)
    # Send abailable homes via Telegram
    if not home_list:
        await update.message.reply_text(f"No homes below {user_price} per month")
        return
    for home in home_list:
        resp = f"🟢 {home['title']}\n"
        resp += f"{home['price']}\n"
        resp += f"{home['url']}"
        await update.message.reply_text(resp)

async def alarm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends alarms of new available homes below a price."""
    # Constants & variables
    chat_id = update.message.chat_id
    timeout = CHECK_TIMEOUT
    known_homes = []
    # Parse price
    if context.args:
        try:
            user_price = int(context.args[0])
        except:
            await update.message.reply_text(f"Invalid price: {context.args[0]}")
            return
    else:
        user_price = 1000
    # Remove previous alarm if exists
    job_removed = remove_job_if_exists(str(chat_id), context)
    # Create new alarm
    data = {
        "price": user_price,
        "known_homes": known_homes
    }
    context.job_queue.run_repeating(alarm_cb, interval=300, first=10, chat_id=chat_id, data=data)
    # Answer
    resp = f"Alarm successfully set. Checking for homes below {user_price} € per month."
    await update.message.reply_text(resp)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends alarms of new available homes below a price."""
    # Constants & variables
    chat_id = update.message.chat_id
    # Remove previous alarm if exists
    job_removed = remove_job_if_exists(str(chat_id), context)
    # Answer
    await update.message.reply_text("Alarm stopped.")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], help_command))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("alarm", alarm))
    application.add_handler(CommandHandler("stop", stop))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
