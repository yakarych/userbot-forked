__all__ = [
    "commands",
]

import json
from typing import Type

from pyrogram import Client
from pyrogram.enums import MessageMediaType, ParseMode
from pyrogram.errors import FileReferenceExpired
from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..storage import Storage
from ..translation import Translation
from ..utils import get_message_content

commands = CommandsModule("Notes")


@commands.add("get", "note", "n", usage="<name>")
async def get_note(
    client: Client,
    message: Message,
    command: CommandObject,
    storage: Storage,
    icons: Type[Icons],
    tr: Translation,
) -> str | None:
    """Sends saved note"""
    _ = tr.gettext
    if not (key := command.args):
        return _("{icon} No name specified").format(icon=icons.WARNING)
    data = await storage.get_note(key)
    if data is None:
        return _("{icon} Message with key={key!r} not found").format(icon=icons.WARNING, key=key)
    content, type_ = json.loads(data[0]), data[1]
    if "caption" in content or "text" in content:
        content["parse_mode"] = ParseMode.HTML
    if type_ == "text":
        await message.edit_text(**content)
        return
    if "message_id" not in content:
        # Backwards compatibility + support for stickers
        try:
            await getattr(client, f"send_{type_}")(
                message.chat.id,
                **content,
                reply_to_message_id=message.reply_to_message_id,
            )
        except FileReferenceExpired:
            return _(
                "{icon} <b>File reference expired, please save the note again.</b>\n"
                "<i>Note key:</i> <code>{key}</code>"
            ).format(icon=icons.WARNING, key=key)
    else:
        await client.copy_message(
            message.chat.id,
            **content,
            reply_to_message_id=message.reply_to_message_id,
        )
    await message.delete()


@commands.add("save", "note_add", "nadd", usage="<reply> <name>")
async def save_note(
    message: Message,
    command: CommandObject,
    storage: Storage,
    notes_chat: int | str,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    """Saves replied message as note for later use"""
    _ = tr.gettext
    if not (key := command.args):
        return _(
            "{icon} Please specify note key\n\n" "Possible fix: <code>{message_text} key</code>"
        ).format(icon=icons.QUESTION, message_text=message.text)
    target = message.reply_to_message
    if target.media not in (MessageMediaType.STICKER, MessageMediaType.WEB_PAGE, None):
        # Stickers and text messages can be saved without problems, other media types should be
        # saved in a chat to be able to send them later even when the original message is deleted.
        target = await target.copy(notes_chat)
    content, type_ = get_message_content(target)
    await storage.save_note(key, json.dumps(content), type_)
    return _("{icon} Note <code>{key}</code> saved").format(icon=icons.BOOKMARK, key=key)


@commands.add("notes", "ns")
async def saved_notes(storage: Storage, icons: Type[Icons], tr: Translation) -> str:
    """Shows all saved notes"""
    _ = tr.gettext
    t = ""
    async for key in storage.saved_notes():
        __, type_ = await storage.get_note(key)
        t += f"• <code>{key}</code> ({type_})\n"
    return _("{icon} <b>Saved notes:</b>\n{t}").format(icon=icons.BOOKMARK, t=t)


@commands.add("note_del", "ndel", usage="<name>")
async def delete_note(
    message: Message,
    command: CommandObject,
    storage: Storage,
    icons: Type[Icons],
    tr: Translation,
) -> str:
    """Deletes saved note"""
    _ = tr.gettext
    if not (key := command.args):
        return _(
            "{icon} Please specify note key\n\n" "Possible fix: <code>{message_text} key</code>"
        ).format(icon=icons.QUESTION, message_text=message.text)
    await storage.delete_note(key)
    return _("{icon} Note <code>{key}</code> deleted").format(icon=icons.TRASH, key=key)
