import nextcord
from nextcord.ext import commands

from plib.terminal import error
# from plib.utils.general import message_deleted
import traceback
from plib.utils.custom_exceptions import BotTypeError

from plib.db_handler import Database as Db
from plib.utils.custom_exceptions import BranchWarning
from cogs.verifier import Button


async def loadPersistentViews(bot: commands.Bot, table: str = "persistent_views"):
    """
    (Alpha) Loads persistent views to bot.
    For now it only works for verifier buttons.

    ## Does not work for now on any other context.

    Parameters
    ----------
    bot : `commands.Bot`
        Bot object.
    table : `str, optional`
        Table name to load persistent views from, by default `"persistent_views"`
    """

    try:
        if not isinstance(bot, commands.Bot):
            raise BotTypeError(bot)
    except BotTypeError as e:
        error(e, traceback.format_exc(), advice= "Please pass a `commands.Bot` object to this function.", level= "ERROR")
        raise

    db = Db()

    data = db.select(table)

    guild_id = int(db.select("basic_info", {"name": "guild_id"})[0][1])

    for label, custom_id, message_id, channel_id in data:
        try:
            guild = await bot.fetch_guild(guild_id)
            channel: nextcord.abc.Messageable = await guild.fetch_channel(channel_id) # pyright: ignore[reportGeneralTypeIssues]
            _ = await channel.fetch_message(message_id)
        except nextcord.errors.NotFound:
            try:
                db.delete(table, {"channel_id": channel_id, "message_id": message_id})
            except BranchWarning:
                pass
            continue
        
        button = Button(label=label, custom_id=custom_id)
        view = nextcord.ui.View(timeout=None)
        view.add_item(button)

        bot.add_view(view=view, message_id=int(message_id))
