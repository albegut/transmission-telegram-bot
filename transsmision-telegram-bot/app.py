import telegram
from telegram.ext import CallbackQueryHandler, CommandHandler, Updater

from . import config, menus, utils


def start(update, context):
    text = menus.menu()
    update.message.reply_text(text, reply_markup=telegram.ReplyKeyboardRemove())


def memory(update, context):
    formatted_memory = menus.get_memory()
    update.message.reply_text(formatted_memory)


def get_torrents_command(update, context):
    torrent_list, keyboard = menus.get_torrents()
    update.message.reply_text(torrent_list, reply_markup=keyboard)


def get_torrents_inline(update, context):
    query = update.callback_query
    callback = query.data.split("_")
    start_point = int(callback[1])
    torrent_list, keyboard = menus.get_torrents(start_point)
    if len(callback) == 3 and callback[2] == "reload":
        try:
            query.edit_message_text(text=torrent_list, reply_markup=keyboard)
            query.answer(text="Reloaded")
        except telegram.error.BadRequest:
            query.answer(text="Nothing to reload")
    else:
        query.answer()
        query.edit_message_text(text=torrent_list, reply_markup=keyboard)


def torrent_menu_inline(update, context):
    query = update.callback_query
    callback = query.data.split("_")
    torrent_id = int(callback[1])
    text, reply_markup = menus.torrent_menu(torrent_id)
    if len(callback) == 3 and callback[2] == "reload":
        try:
            query.edit_message_text(text=text, reply_markup=reply_markup)
            query.answer(text="Reloaded")
        except telegram.error.BadRequest:
            query.answer(text="Nothing to reload")
    else:
        query.answer()
        query.edit_message_text(text=text, reply_markup=reply_markup)


def torrent_files_inline(update, context):
    query = update.callback_query
    callback = query.data.split("_")
    torrent_id = int(callback[1])
    text, reply_markup = menus.get_files(torrent_id)
    if len(callback) == 3 and callback[2] == "reload":
        try:
            query.edit_message_text(text=text, reply_markup=reply_markup)
            query.answer(text="Reloaded")
        except telegram.error.BadRequest:
            query.answer(text="Nothing to reload")
    else:
        query.answer()
        query.edit_message_text(text=text, reply_markup=reply_markup)


def run():
    bot = telegram.Bot(token=config.TOKEN)
    updater = Updater(token=config.TOKEN)
    utils.setup_ngrok_webhook(updater)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("menu", start))
    updater.dispatcher.add_handler(CommandHandler("memory", memory))
    updater.dispatcher.add_handler(CommandHandler("torrents", get_torrents_command))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(torrent_files_inline, pattern="torrentsfiles_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(get_torrents_inline, pattern="torrentsgoto_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(torrent_menu_inline, pattern="torrent_*")
    )
    print(bot.get_me())
    updater.idle()
