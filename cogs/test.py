import nextcord
from nextcord import Interaction
from nextcord.ext import commands
import os

guild_id = int(os.environ["guild_id"])

class Test (commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    @nextcord.slash_command(guild_ids=[guild_id], force_global=True,
                            description="Description")
    async def test_command(self, interaction: Interaction):
        # code here
        pass

def setup(bot: commands.Bot):
    # pylint: disable=missing-function-docstring
    bot.add_cog(Test(bot))
