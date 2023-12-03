from discord import TextChannel
import nextcord
from nextcord.ext import commands, ipc
import os

guild_id = int(os.environ["guild_id"])

class NewsPaper(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @ipc.server.route()
    async def publish(self, data):
        page_data = data.page_data
        payload_embeds = list()
        embed_title = nextcord.Embed(
            title= "¡Nueva tarea encontrada!",
            color= 0x825bca,
            description=   (f"Tarea de {page_data['name']}\n\n" +
                            "Parece ser que se ha encontrado una nueva tarea en el campus. " +
                            "Podría tratarse de una tarea nueva o de una tarea modificada. " +
                            "También podría ser una tarea erróneamente publicada.")
        )
        payload_embeds.append(embed_title)

        content_description = f"Contenido encontrado: \n\n{page_data['content'][:4000:]}"
        if len(page_data["content"]) > 4001:
            content_description += "\n\n[...]"
        embed_content = nextcord.Embed(
            title= f"[{page_data["title"]}]({page_data['link']})",
            color= 0x4c327c,
            description= content_description
        )
        payload_embeds.append(embed_content)

        if page_data["urls"]:                
            urls_description = "Se han encontrado una serie de enlaces que podrían resultar útiles: \n\n"
            for url in page_data["urls"]:
                section = f'- {url["text"]}\n  - {url["link"]}\n\n'

                if len(urls_description) + len(section) > 4001:
                    urls_description += "\n\n[...] demasiados enlaces para mostrar..."
                    break
                
                urls_description += section

            embed_urls = nextcord.Embed(
                title= "Posibles enlaces",
                color= 0x4c327c,
                description= urls_description
            )
            payload_embeds.append(embed_urls)
        else:
            embed_urls = None
        

        guild = self.bot.get_guild(guild_id)
        channel: TextChannel = guild.get_channel(1157581624423239761)

        webhooks = await channel.webhooks()
        print(f"Publishing {page_data['title']}...")
        await webhooks[0].send(
            username= "Vigilante",
            embeds= payload_embeds,
            avatar_url= "https://media.discordapp.net/attachments/1156462946101248040/1177961564104556705/ojo-morado-tiempo-188132-4003427999.png?ex=65746932&is=6561f432&hm=35916669e3dc8e1bbfda095b8c6d2208d17de56cc2921488cb799cd216239f4d&=&format=webp&width=832&height=468https://media.discordapp.net/attachments/1156462946101248040/1177961564104556705/ojo-morado-tiempo-188132-4003427999.png?ex=65746932&is=6561f432&hm=35916669e3dc8e1bbfda095b8c6d2208d17de56cc2921488cb799cd216239f4d&=&format=webp&width=832&height=468"
            )

    @ipc.server.route()
    async def status(self, data):
        return 200

def setup(bot: commands.Bot):
    # pylint: disable=missing-function-docstring
    bot.add_cog(NewsPaper(bot))
