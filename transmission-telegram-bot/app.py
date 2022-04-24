import logging
import os
from pickle import TRUE
import time
from typing import Any
import telegram
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    Updater,
)
from telegram.ext.filters import Filters

from . import config, menus, utils

@utils.whitelist
def start(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    text = menus.menu()
    update.message.reply_text(text, reply_markup=telegram.ReplyKeyboardRemove())


@utils.whitelist
def add(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    text = menus.add_torrent()
    update.message.reply_text(text)


@utils.whitelist
def memory(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    formatted_memory = menus.get_memory()
    update.message.reply_text(formatted_memory)


@utils.whitelist
def get_torrents_command(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    torrent_list, keyboard = menus.get_torrents()
    update.message.reply_text(
        torrent_list, reply_markup=keyboard, parse_mode="MarkdownV2"
    )


@utils.whitelist
def get_torrents_inline(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query = update.callback_query
    callback = query.data.split("_")
    start_point = int(callback[1])
    torrent_list, keyboard = menus.get_torrents(start_point)
    if len(callback) == 3 and callback[2] == "reload":
        try:
            query.edit_message_text(
                text=torrent_list, reply_markup=keyboard, parse_mode="MarkdownV2"
            )
            query.answer(text="Reloaded")
        except telegram.error.BadRequest:
            query.answer(text="Nothing to reload")
    else:
        query.answer()
        query.edit_message_text(
            text=torrent_list, reply_markup=keyboard, parse_mode="MarkdownV2"
        )


@utils.whitelist
def torrent_menu_inline(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query = update.callback_query
    callback = query.data.split("_")
    torrent_id = int(callback[1])
    if len(callback) == 3 and callback[2] != "reload":
        if callback[2] == "start":
            menus.start_torrent(torrent_id)
            query.answer(text="Started")
            time.sleep(0.2)
        elif callback[2] == "stop":
            menus.stop_torrent(torrent_id)
            query.answer(text="Stopped")
            time.sleep(0.2)
        elif callback[2] == "verify":
            menus.verify_torrent(torrent_id)
            query.answer(text="Verifying")
            time.sleep(0.2)
    try:
        text, reply_markup = menus.torrent_menu(torrent_id)
    except KeyError:
        query.answer(text="Torrent no longer exists")
        text, reply_markup = menus.get_torrents()
        query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
        )
    else:
        if len(callback) == 3 and callback[2] == "reload":
            try:
                query.edit_message_text(
                    text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
                )
                query.answer(text="Reloaded")
            except telegram.error.BadRequest:
                query.answer(text="Nothing to reload")
        else:
            query.answer()
            query.edit_message_text(
                text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
            )


@utils.whitelist
def torrent_files_inline(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query = update.callback_query
    callback = query.data.split("_")
    torrent_id = int(callback[1])
    try:
        text, reply_markup = menus.get_files(torrent_id)
    except KeyError:
        query.answer(text="Torrent no longer exists")
        text, reply_markup = menus.get_torrents()
        query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
        )
    else:
        if len(callback) == 3 and callback[2] == "reload":
            try:
                query.edit_message_text(
                    text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
                )
                query.answer(text="Reloaded")
            except telegram.error.BadRequest:
                query.answer(text="Nothing to reload")
        else:
            query.answer()
            query.edit_message_text(
                text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
            )


@utils.whitelist
def delete_torrent_inline(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    torrent_id = int(callback[1])
    try:
        text, reply_markup = menus.delete_menu(torrent_id)
    except KeyError:
        query.answer(text="Torrent no longer exists")
        text, reply_markup = menus.get_torrents()
        query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
        )
    else:
        query.answer()
        query.edit_message_text(text=text, reply_markup=reply_markup)


@utils.whitelist
def delete_torrent_action_inline(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    torrent_id = int(callback[1])
    if len(callback) == 3 and callback[2] == "data":
        menus.delete_torrent(torrent_id, True)
    else:
        menus.delete_torrent(torrent_id)
    query.answer(text="✅Deleted")
    time.sleep(0.1)
    torrent_list, keyboard = menus.get_torrents()
    query.edit_message_text(
        text=torrent_list, reply_markup=keyboard, parse_mode="MarkdownV2"
    )


@utils.whitelist
def torrent_file_handler(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    file_bytes = context.bot.get_file(update.message.document).download_as_bytearray()
    torrent = menus.add_torrent_with_file(file_bytes)
    update.message.reply_text("Torrent added", quote=True)
    text, reply_markup = menus.add_menu(torrent.id)
    update.message.reply_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )

@utils.whitelist
def url_handler(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    text, reply_markup = menus.add_FirstStep()
    update.message.reply_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )
    f = open(f"urlinfo_{update.message.from_user.id}.txt", "w")
    f.write(update.message.text)
    f.close()

@utils.whitelist
def tvShow_handler(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    #msg = context.bot.send_message(update.callback_query.message.chat.id, 'Enter tmfs separated with space: ')
    #context.bot.register_next_step_handler(msg,update.callback_query.from_user.id, tvShow_handler_nextStep)
    query: telegram.CallbackQuery = update.callback_query
    text, reply_markup = menus.add_TVShow_FolderMenu()
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )

@utils.whitelist
def tvShow_folder_handler(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    text, reply_markup = menus.season_menu(callback[1],None)
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )

@utils.whitelist
def tvShow_seasonfolder_handler(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    text, reply_markup = menus.season_menu(callback[1],callback[2])
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )

@utils.whitelist
def newTvShow_handler(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    query.edit_message_text(
        text="Enter new tv show name", parse_mode="MarkdownV2"
    )

@utils.whitelist
def tvShow_finish_handler(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    f = open(f"urlinfo_{update.callback_query.from_user.id}.txt", "r")
    torrent = menus.add_torrent_with_url(f.read(), f"{config.TV_FOLDER}/{callback[1]}/T{callback[2]}")
    text, reply_markup = menus.add_menu(torrent.id)
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )
    

@utils.whitelist
def tvShow_handler_nextStep(msg: any, userId:any,context: CallbackContext[Any, Any, Any]):
    logging.warning(msg)
    f = open(f"urlinfo_{userId}.txt", "r")
    torrent = menus.add_torrent_with_url(f.read(), config.TV_FOLDER)
    text, reply_markup = menus.add_menu(torrent.id)
    #query.edit_message_text(
    #    text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    #)

@utils.whitelist
def film_handler(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    f = open(f"urlinfo_{update.callback_query.from_user.id}.txt", "r")
    torrent = menus.add_torrent_with_url(f.read(), config.FILMS_FOLDER)
    text, reply_markup = menus.add_menu(torrent.id)
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )
      

@utils.whitelist
def torrent_adding_actions(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    if len(callback) == 3:
        torrent_id = int(callback[1])
        if callback[2] == "start":
            menus.start_torrent(torrent_id)
            text, reply_markup = menus.started_menu(torrent_id)
            query.answer(text="✅Started")
            query.edit_message_text(
                text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
            )
        elif callback[2] == "cancel":
            menus.delete_torrent(torrent_id, True)
            query.answer(text="✅Canceled")
            query.edit_message_text("Torrent deleted🗑")


@utils.whitelist
def torrent_adding(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    torrent_id = int(callback[1])
    text, reply_markup = menus.add_menu(torrent_id)
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )


@utils.whitelist
def edit_file(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    torrent_id = int(callback[1])
    file_id = int(callback[2])
    to_state = int(callback[3])
    menus.torrent_set_files(torrent_id, file_id, bool(to_state))
    query.answer()
    text, reply_markup = menus.get_files(torrent_id)
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )


@utils.whitelist
def select_for_download(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    torrent_id = int(callback[1])
    text, reply_markup = menus.select_files_add_menu(torrent_id)
    query.answer()
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )


@utils.whitelist
def select_file(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    torrent_id = int(callback[1])
    file_id = int(callback[2])
    to_state = int(callback[3])
    menus.torrent_set_files(torrent_id, file_id, bool(to_state))
    query.answer()
    text, reply_markup = menus.select_files_add_menu(torrent_id)
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )


@utils.whitelist
def settings_menu_command(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    text, reply_markup = menus.settings_menu()
    update.message.reply_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )

@utils.whitelist
def restart(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    os.system("sudo systemctl restart transmission-daemon")
    os.system("sudo systemctl restart smbd.service")
    update.message.reply_text(
        text="✅ Services restarted", parse_mode="MarkdownV2"
    )



@utils.whitelist
def settings_menu_inline(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    text, reply_markup = menus.settings_menu()
    query.answer()
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )


@utils.whitelist
def change_server_menu_inline(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    text, reply_markup = menus.change_server_menu(int(callback[1]))
    query.answer()
    query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )


@utils.whitelist
def change_server_inline(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    query: telegram.CallbackQuery = update.callback_query
    callback: list[str] = query.data.split("_")
    success = menus.change_server(int(callback[1]))
    text, reply_markup = menus.change_server_menu(int(callback[2]))
    if success:
        query.answer("✅Success")
    else:
        query.answer("❌Error❌")
    try:
        query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode="MarkdownV2"
        )
    except telegram.error.BadRequest:
        pass


@utils.whitelist
def error_handler(update: telegram.Update, context: CallbackContext[Any, Any, Any]):
    text = "Something went wrong"
    logging.error('Update "%s" caused error "%s"', update, context.error)
    if update.callback_query:
        query: telegram.CallbackQuery = update.callback_query
        query.edit_message_text(text=text, parse_mode="MarkdownV2")
    else:
        update.message.reply_text(text)


def run():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    updater = Updater(token=config.TOKEN)
    utils.setup_updater(updater)
    updater.dispatcher.add_error_handler(error_handler)
    updater.dispatcher.add_handler(
        MessageHandler(Filters.document.file_extension("torrent"), torrent_file_handler)
    )
    updater.dispatcher.add_handler(
        MessageHandler(Filters.regex(r"\Amagnet:\?xt=urn:btih:.*"), url_handler, pass_user_data=TRUE)
    )
    updater.dispatcher.add_handler(
        MessageHandler(Filters.regex(".*\.torrent"), url_handler, pass_user_data=TRUE)
    )
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("menu", start))
    updater.dispatcher.add_handler(CommandHandler("add", add))
    updater.dispatcher.add_handler(CommandHandler("memory", memory))
    updater.dispatcher.add_handler(CommandHandler("torrents", get_torrents_command))
    updater.dispatcher.add_handler(CommandHandler("settings", settings_menu_command))
    updater.dispatcher.add_handler(CommandHandler("restart", restart))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(settings_menu_inline, pattern="settings")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(change_server_inline, pattern="server\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(change_server_menu_inline, pattern="changeservermenu\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(torrent_adding, pattern="addmenu\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(select_file, pattern="fileselect\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(select_for_download, pattern="selectfiles\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(edit_file, pattern="editfile\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(torrent_adding_actions, pattern="torrentadd\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(torrent_files_inline, pattern="torrentsfiles\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(delete_torrent_inline, pattern="deletemenutorrent\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(delete_torrent_action_inline, pattern="deletetorrent\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(get_torrents_inline, pattern="torrentsgoto\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(torrent_menu_inline, pattern="torrent\\_*")
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(tvShow_handler, pattern="isTvShow\\_*", pass_chat_data=True)
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(film_handler, pattern="isFilm\\_*", pass_user_data=True)
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(tvShow_folder_handler, pattern="TvShowfolder\\_*", pass_user_data=True)
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(tvShow_seasonfolder_handler, pattern="addSeson\\_*", pass_user_data=True)
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(tvShow_finish_handler, pattern="finishSeason\\_*", pass_user_data=True)
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(newTvShow_handler, pattern="TvNewShowfolder\\_*", pass_user_data=True)
    )
    
    updater.bot.set_my_commands(
        [
            ("start", "Open menu with commands"),
            ("menu", "Open menu with commands"),
            ("torrents", "List all torrents"),
            ("memory", "Available memory"),
            ("add", "Add torrent"),
            ("restart", "Restart raspberry services"),
            ("settings", "Bot settings"),
        ]
    )
    user: dict[str, str] = updater.bot.get_me()
    logger.info(f"Started bot {user['first_name']} at https://t.me/{user['username']}")
    updater.idle()
