__all__ = ["commands"]

from typing import Type

from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule
from ..storage import Storage
from ..translation import Translation

commands = CommandsModule("Language")


@commands.add("lang", usage="[language-code]")
async def chat_language(
    message: Message,
    command: CommandObject,
    storage: Storage,
    icons: Type[Icons],
    tr: Translation,
    lang: str | None,
) -> str:
    """Get or change the language of the bot for the current chat"""
    # Mark the flag as translatable string but don't translate it here yet
    _ = lambda x: x
    # i18n: flag must be country flag for the language
    flag = _("🏳")

    _ = tr.gettext
    if not command.args:
        languages = ""
        for language in tr.get_available_languages():
            languages += f"• <code>{language}</code>\n"
        return _(
            "{icon} Current chat language: {flag} {lang}\n\n"
            "To change it, type <code>{message_text} code</code>\n"
            "Available languages:\n{languages}"
        ).format(
            icon=icons.GLOBE,
            flag=_(flag),
            lang=lang,
            message_text=message.text,
            languages=languages,
        )
    new_lang = command.args[0]
    if new_lang not in tr.get_available_languages:
        return _("{icon} Invalid language code").format(icon=icons.WARNING)
    await storage.set_chat_language(message.chat.id, new_lang)
    # Change the language on-the-fly for middlewares and current handler
    tr.change_language(new_lang)
    return _("{icon} Language changed to {flag} {lang}").format(
        icon=icons.GLOBE,
        flag=_(flag),
        lang=new_lang,
    )
