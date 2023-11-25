from operator import ne
from pprint import pp
from discord import TextChannel
import nextcord
from nextcord import Interaction
from nextcord.ext import commands, ipc

from plib.db_handler import Database as Db

db = Db()
guild_id = int(db.select("basic_info", {"name": "guild_id"})[0][1])
del db

class NewsPaper(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    # @nextcord.slash_command(guild_ids=[guild_id], force_global=True,
    #                         description="Description")
    # async def test_command(self, interaction: Interaction):
    #     # code here
    #     pass
    
    @ipc.server.route()
    async def publish(self, data):
        pageData = data.pageData
        payloadEmbeds = list()
        embedTitle = nextcord.Embed(
            title= "¡Nueva tarea encontrada!",
            color= 0x825bca,
            description=   (f"Tarea de {pageData['name']}\n\n" +
                            "Parece ser que se ha encontrado una nueva tarea en el campus. " +
                            "Podría tratarse de una tarea nueva o de una tarea modificada. " +
                            "También podría ser una tarea erróneamente publicada.")
        )
        embedTitle.set_thumbnail(url= pageData["link"])
        payloadEmbeds.append(embedTitle)

        contentDescription = f"Contenido encontrado: \n\n{pageData['content'][:4000:]}"
        if len(pageData["content"]) > 4001:
            contentDescription += "\n\n[...]"
        embedContent = nextcord.Embed(
            title= pageData["title"],
            color= 0x4c327c,
            description= contentDescription
        )
        payloadEmbeds.append(embedContent)

        if pageData["urls"]:                
            urlsDescription = "Se han encontrado una serie de enlaces que podrían resultar útiles: \n\n"
            for url in pageData["urls"]:
                section = f'- {url["text"]}\n  - {url["link"]}\n\n'

                if len(urlsDescription) + len(section) > 4001:
                    urlsDescription += "\n\n[...] demasiados enlaces para mostrar..."
                    break

            embedUrls = nextcord.Embed(
                title= "Posibles enlaces",
                color= 0x4c327c,
                description= urlsDescription
            )
            payloadEmbeds.append(embedUrls)
        else:
            embedUrls = None
        

        guild = self.bot.get_guild(guild_id)
        channel: TextChannel = guild.get_channel(1157581624423239761)

        webhooks = await channel.webhooks()
        print(f"Publishing {pageData['title']}...")
        await webhooks[0].send(
            username= "Vigilante",
            embeds= payloadEmbeds,
            avatar_url= "https://media.discordapp.net/attachments/1156462946101248040/1177961564104556705/ojo-morado-tiempo-188132-4003427999.png?ex=65746932&is=6561f432&hm=35916669e3dc8e1bbfda095b8c6d2208d17de56cc2921488cb799cd216239f4d&=&format=webp&width=832&height=468https://media.discordapp.net/attachments/1156462946101248040/1177961564104556705/ojo-morado-tiempo-188132-4003427999.png?ex=65746932&is=6561f432&hm=35916669e3dc8e1bbfda095b8c6d2208d17de56cc2921488cb799cd216239f4d&=&format=webp&width=832&height=468"
            )

    @ipc.server.route()
    async def status(self, data):
        return 200

def setup(bot: commands.Bot):
    # pylint: disable=missing-function-docstring
    bot.add_cog(NewsPaper(bot))
