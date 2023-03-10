# ------------------------------- Import ------------------------------- #
import json
from telegram.ext import MessageHandler, Filters, ConversationHandler, CommandHandler, ChatMemberHandler
from telegram import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ParseMode
from telegram.utils.helpers import create_deep_linked_url

from settings import config
import utils
from . import BOT, button as btn, text as txt
from time import sleep


# ---------------------------- File Uploader --------------------------- #
class FileUploader(BOT):
    def __init__(self):
        # Handlers
        self.MESSAGE = range(1)

        self.handlers = [
            ChatMemberHandler(self.chat_member_handler, ChatMemberHandler.ANY_CHAT_MEMBER),
            CommandHandler(txt.start_cmd, self.start_file, Filters.regex(txt.start_file_regex)),
            CommandHandler(txt.start_cmd, self.start_bot),
            CommandHandler(txt.channel_data_cmd, self.edit_channel_data),
            CommandHandler(txt.admin_data_cmd, self.edit_admin_data),
            MessageHandler(
                Filters.chat_type.private and Filters.document, self.add_file
            ),
            ConversationHandler(
                entry_points=[
                    CommandHandler(txt.send_all_cmd, self.get_message),
                ],
                states={
                    self.MESSAGE: [
                        MessageHandler(
                            Filters.all and ~Filters.command(txt.cancel_cmd), self.send_all
                        )
                    ],
                },
                fallbacks=[
                    CommandHandler(txt.cancel_cmd, self.cancel),
                ]
            ),
        ]

    # ------------------------------------------------------------ #
    # Static
    def cancel(self, update, context):
        CID = update.effective_chat.id
        text = txt.back_menu
        context.bot.send_message(CID, text)
        return ConversationHandler.END

    # ------------------------------------------------------------ #
    # Chat Member Handler
    def chat_member_handler(self, update, context):
        UID = update.effective_user.id
        data = utils.get_data()
        users = data['USERS']

        status = update.my_chat_member.new_chat_member.status
        if status == 'kicked':
            users.remove(UID)
        elif status == 'member':
            users.append(UID)
        else:
            text = f'[ChatMemberHandler]\n<code>{str(update)}</code>'
            return context.bot.send_message(
                config.OWNER, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )

        utils.update_data(data)

        # {'my_chat_member': {'new_chat_member': {'status': 'kicked', 'user': {'is_bot': True, 'first_name': 'Programming Test Bot', 'id': 5561789726, 'username': 'habib_test_bot'}, 'until_date': 0}, 'date': 1678462679, 'old_chat_member': {'status': 'member', 'user': {'is_bot': True, 'first_name': 'Programming Test Bot', 'id': 5561789726, 'username': 'habib_test_bot'}, 'until_date': None}, 'chat': {'type': 'private', 'last_name': 'H', 'id': 5782575795, 'first_name': 'H', 'username': 'hossein_habibi_2004'}, 'from': {'is_bot': False, 'first_name': 'H', 'last_name': 'H', 'id': 5782575795, 'username': 'hossein_habibi_2004', 'language_code': 'en'}}, 'update_id': 286790027}
        # {'my_chat_member': {'new_chat_member': {'status': 'member', 'user': {'is_bot': True, 'first_name': 'Programming Test Bot', 'id': 5561789726, 'username': 'habib_test_bot'}, 'until_date': None}, 'date': 1678462686, 'old_chat_member': {'status': 'kicked', 'user': {'is_bot': True, 'first_name': 'Programming Test Bot', 'id': 5561789726, 'username': 'habib_test_bot'}, 'until_date': 0}, 'chat': {'type': 'private', 'last_name': 'H', 'id': 5782575795, 'first_name': 'H', 'username': 'hossein_habibi_2004'}, 'from': {'is_bot': False, 'first_name': 'H', 'last_name': 'H', 'id': 5782575795, 'username': 'hossein_habibi_2004', 'language_code': 'en'}}, 'update_id': 286790028}

    # ------------------------------------------------------------ #
    # Start Bot
    def start_bot(self, update, context):
        UID = update.effective_user.id

        data = utils.get_data()
        if not self.is_user(UID):
            data['USERS'].append(UID)
        utils.update_data(data)

        text = txt.start_bot_text
        context.bot.send_message(
            UID, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )

    # ------------------------------------------------------------ #
    # Start File
    def start_file(self, update, context):
        UID = update.effective_user.id
        FID = update.message.text.replace(f"/{txt.start_cmd} file_", "")
        MID = update.message.message_id

        data = utils.get_data()
        if not self.is_user(UID):
            data['USERS'].append(UID)

        files = data['FILES']
        if self.is_member_in_channels(UID, context.bot):
            file = files[FID]
            file['download_count'] += 1
            if self.is_admin(UID):
                text = f"?????????? ????????????: {file['download_count']}\n"
            else:
                text = txt.bot_text
            context.bot.send_document(
                chat_id=UID, document=file['file_id'], caption=text, reply_to_message_id=MID, parse_mode=ParseMode.HTML
            )
        else:
            channels = data['MAIN_CHANNELS'] + data['CHANNELS']
            keyboard = []
            for channel_id in channels:
                try:
                    channel = context.bot.get_chat(channel_id)
                    if channel.invite_link != None:
                        keyboard.append(
                            [IKB(text=channel.title, url=channel.invite_link)]
                        )
                except Exception as e:
                    context.bot.send_message(
                        config.OWNER, f'[ERROR] (Get File)\n<a href="{create_deep_linked_url(context.bot.username, f"file_{FID}")}">File</a>\n\n{e}', parse_mode=ParseMode.HTML, disable_web_page_preview=True
                    )
            text = txt.start_file_text.format(url=create_deep_linked_url(context.bot.username, f"file_{FID}"))
            context.bot.send_message(UID, text, reply_markup=IKM(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            # keyboard.append([IKB(text='Download File', url=create_deep_linked_url(context.bot.username, f"file_{FID}"))])
        utils.update_data(data)


    # ------------------------------------------------------------ #
    # Add File
    def add_file(self, update, context):
        UID = update.effective_user.id
        data = utils.get_data()
        files = data['FILES']

        document = update.message.document
        if document.file_unique_id not in files:
            files[document.file_unique_id] = {
                'file_id': document.file_id,
                'download_count': 0
            }
        utils.update_data(data)

        text = create_deep_linked_url(context.bot.username, f"file_{document.file_unique_id}")
        context.bot.send_message(
            UID, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )

    # ------------------------------------------------------------ #
    # Channel Data
    def edit_channel_data(self, update, context):
        UID = update.effective_user.id
        channel_data = update.message.text.replace(f'/{txt.channel_data_cmd} ', '')

        data = utils.get_data()
        channels = data['CHANNELS']
        if self.is_admin(UID):
            if channel_data == f'/{txt.channel_data_cmd}':
                send_to = UID
                text = '?????????? ?????? ????????:\n'
                for channel_id in channels:
                    channel = context.bot.get_chat(channel_id)
                    if channel.invite_link != None:
                        text += f'??? <a href="{channel.invite_link}">{channel.title}</a>\n'
                    else:
                        text += f'??? <a href="https://t.me/{channel.username}">{channel.title}</a>\n'
            else:
                try:
                    if channel_data.isdigit():
                        if not channel_data.startswith('-100'):
                            channel_data = '-100' + channel_data
                    else:
                        if '/' in channel_data:
                            channel_data = channel_data.split('/')[-1]
                        if not channel_data.startswith('@'):
                            channel_data = '@' + channel_data

                    channel = context.bot.get_chat(channel_data)
                    if channel.type == 'channel':
                        if channel.id not in channels:
                            channels.append(channel.id)
                            send_to = UID
                            text = f'??? ?????? <b>{channel.title}</b> ?????????? ????.'
                        else:
                            channels.remove(channel.id)
                            send_to = UID
                            text = f'??? ?????? <b>{channel.title}</b> ?????? ????.'
                        utils.update_data(data)
                    else:
                        send_to = UID
                        text = '?????????? ??????????????.'
                except Exception as e:
                    if str(e) == 'Chat not found':
                        send_to = UID
                        text = "???????? ???? ?????? ?????? ????????."
                    else:
                        send_to = config.OWNER
                        text = f'[COMMAND]\n{update.message.text}\n\n[ERROR]\n{str(e)}'

            return context.bot.send_message(
                send_to, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )

    # ------------------------------------------------------------ #
    # Admin Data
    def edit_admin_data(self, update, context):
        UID = update.effective_user.id
        user_data = update.message.text.replace(f'/{txt.admin_data_cmd} ', '')

        data = utils.get_data()
        admins = data['ADMINS']
        if self.is_owner(UID):
            if user_data == f'/{txt.admin_data_cmd}':
                text = '?????????????????:\n'
                for admin_id in admins:
                    admin = context.bot.get_chat(admin_id)
                    text += f'<a href="https://t.me/{admin.username}">{admin.first_name} {admin.last_name}</a>\n'
            else:
                if not user_data.isdigit():
                    if '/' in user_data:
                        user_data = user_data.split('/')[-1]
                    if not user_data.startswith('@'):
                        user_data = '@' + user_data

                try:
                    user = context.bot.get_chat(user_data)
                    if user.type == 'private':
                        if user.id not in admins:
                            admins.append(user.id)
                            text = f'??? ?????????? <b>{user.first_name} {user.last_name}</b> ?????????? ????.'
                        else:
                            admins.remove(user.id)
                            text = f'??? ?????????? <b>{user.first_name} {user.last_name}</b> ???? ???????? ????????????????? ?????? ????.'
                        utils.update_data(data)
                    else:
                        text = '?????????? ??????????????.'
                except Exception as e:
                    text = f'[COMMAND]\n{update.message.text}\n\n[ERROR]\n{str(e)}'

            return context.bot.send_message(
                UID, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )

    # ------------------------------------------------------------ #
    # Send All
    def get_message(self, update, context):
        UID = update.effective_user.id
        if self.is_admin(UID):
            text = txt.get_message
            context.bot.send_message(UID, text)
            return self.MESSAGE

    def send_all(self, update, context):
        UID = update.effective_user.id
        users = utils.get_data()['USERS']

        sended_count, error_count = 0, 0
        for user_id in users:
            try:
                context.bot.copy_message(user_id, UID, update.message.message_id, parse_mode=ParseMode.HTML)
                sended_count += 1
            except Exception as e:
                context.bot.send_message(
                    config.OWNER, f"[ERROR] (Send All)\n{e}", parse_mode=ParseMode.HTML, disable_web_page_preview=True
                )
                error_count += 1
            sleep(0.5)

        text = f"?????????? ???????? ???? ?????????????? ???? ?????????? ????????.\n??? ?????????? ?????????? ?????????? ?????? : {sended_count}\n??? ?????????? ?????????? ?????????? ???????? : {error_count}"
        context.bot.send_message(
            UID, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )
        return ConversationHandler.END
