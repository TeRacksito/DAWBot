from math import e
import sys
from discord import Permissions
import nextcord
from nextcord import Interaction
from nextcord.ext import commands
import os

guild_id = int(os.environ["guild_id"])

class Restarting (commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot

    @nextcord.slash_command(guild_ids=[guild_id], force_global=True,
                            description="Restart the bot.",
                            default_member_permissions=Permissions(administrator=True))
    async def restart(self, interaction: Interaction):
        """
        (alpha) Restart the bot.
        """
        message = ("Exiting with code 100 on restart purpose.\n"+
                   "This is meant to be used with a service manager like systemd.\n\n"+
                   "If you are not using a service manager, then the bot will not restart.")
        
        # For the future: This should be changed to a proper drop-menu, with a confirmation.
        # Maybe also autodetect if the bot is running with a service manager or not.
        await interaction.send(message, ephemeral=True)
        print(message)

        sys.exit(100)
    
    @nextcord.slash_command(guild_ids=[guild_id], force_global=True,
                            name="reload-commands",
                            description="Restart commands.",
                            default_member_permissions=Permissions(administrator=True))
    async def reload_commands(self, interaction: Interaction):
        """
        (alpha) Reloads all commands.
        """
        await interaction.response.defer(ephemeral= True)

        print("Reloading commands.")
        await self.bot.discover_application_commands()

        await interaction.send("Commands reloaded.", ephemeral=True)

def setup(bot: commands.Bot):
    # pylint: disable=missing-function-docstring
    bot.add_cog(Restarting(bot))
