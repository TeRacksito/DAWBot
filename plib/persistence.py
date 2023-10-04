import nextcord
from nextcord.ext import commands

from plib.terminal import error
from plib.utils.general import message_deleted
import traceback
from plib.utils.custom_exceptions import BotTypeError

from plib.db_handler import Database as Db
from cogs.verifier import Button


async def loadPersistentViews(bot: commands.Bot, table: str = "persistent_views"):
    """
    (Alpha) Loads persistent views to bot.
    For now it only works for verifier buttons.

    Parameters
    ----------
    bot : `commands.Bot`
        _description_
    table : `str, optional`
        _description_, by default `"persistent_views"`
    """

    try:
        if not isinstance(bot, commands.Bot):
            raise BotTypeError(bot)
    except BotTypeError as e:
        error(e, traceback.format_exc())

    db = Db()

    data = db.select(table)

    await bot.fetch_channel(23123)

    for label, custom_id, message_id in data:
        button = Button(label=label, custom_id=custom_id)
        view = nextcord.ui.View(timeout=None)
        view.add_item(button)

        bot.add_view(view=view, message_id=int(message_id))
