import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from cooldowns import define_shared_cooldown, shared_cooldown, SlashBucket, CallableOnCooldown

class Verificator (commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    @nextcord.slash_command(guild_ids= [1156345547788136539], force_global= True,
                            description= "Description")
    async def verification (self, interaction: Interaction):
        pass

# Setup
def setup(bot):
    # pylint: disable=missing-function-docstring
    bot.add_cog(Verificator(bot))