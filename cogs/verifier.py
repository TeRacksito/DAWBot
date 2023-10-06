from typing import List

import nextcord
from nextcord import Interaction
from nextcord.emoji import Emoji
from nextcord.enums import ButtonStyle
from nextcord.ext import commands
from nextcord.partial_emoji import PartialEmoji

from plib.db_handler import Database as Db
from plib.utils.custom_exceptions import BranchWarning

db = Db()
guild_id = int(db.select("basic_info", {"name": "guild_id"})[0][1])
del db


class Modal (nextcord.ui.Modal):
    def __init__(self, title: str, *, timeout: float | None = None, auto_defer: bool = True) -> None:
        super().__init__(title, timeout=timeout, auto_defer=auto_defer)

        # self.add_item("TestTestTestTestTestTestTestTestTestTest")

        self.question = nextcord.ui.TextInput(
            label="Nombre y Apellidos",
            style=nextcord.TextInputStyle.short,
            placeholder="Copialo exactamente igual que en el Campus.",
            required=True,
            min_length=10,
            row=0
        )
        # self.children.append(self.question)
        self.add_item(self.question)

    async def callback(self, interaction: Interaction) -> None:

        await interaction.response.defer()
        print(self.question.value)

        db = Db()

        
        users: List[tuple[str, int]] = db.select("users") # pyright: ignore[reportGeneralTypeIssues]

        for user in users:

            if self.question.value in user:

                name: str = user[0]
                on_use = user[1]

                if on_use == bytearray(b'1'):
                    channel = await interaction.user.create_dm()

                    embed = nextcord.Embed(
                        color=0xc60f33,
                        title="Error al verificar.",
                        description="Parece ser que tu usuario ya ha sido registrado..." +
                        "\nSiempre puedes pedir ayuda en el servidor si esto se trata de un error."
                    )
                    await channel.send(embed=embed)
                    return None

                else:
                    try:
                        db.update(table="users", key_name="name",
                              key_value=name, value_name="on_use", value_value=1)
                    except BranchWarning:
                        channel = await interaction.user.create_dm()

                        embed = nextcord.Embed(
                            color=0xc60f33,
                            title="Developer mode.",
                            description="Bot en modo developer." +
                            "\nNo se ha guardado de forma permanente la verificación."
                        )
                        await channel.send(embed=embed)

                    role_verification = interaction.guild.get_role(
                        1156453646649798726)
                    role_daw = interaction.guild.get_role(1156910626153705553)
                    role_daw_new = interaction.guild.get_role(
                        1156454566854938655)

                    user_id = interaction.user.id

                    await interaction.guild.get_member(user_id).add_roles(                        
                        role_verification, # pyright: ignore[reportGeneralTypeIssues]
                        role_daw,  # pyright: ignore[reportGeneralTypeIssues]
                        reason="Verified User by DAW bot"
                    )

                    await interaction.guild.get_member(user_id).remove_roles(
                        role_daw_new, # pyright: ignore[reportGeneralTypeIssues]
                        reason="Verified User by DAW bot"
                    )

                    # interaction.user.add_roles(
                    #     roles= [role_verification, role_daw],
                    #     reason= "Verified User by DAW bot"
                    # )

                    nick = name.split(" ")[0] + " " + \
                        name.split(" ")[1][0] + "."

                    await interaction.guild.get_member(user_id).edit(nick=nick)

                    channel = await interaction.user.create_dm()

                    embed = nextcord.Embed(
                        color=0x00558e,
                        title="Verificación de alumno DAW.",
                        description="Se te ha verificado satisfactoriamente." +
                        "\nAhora deberías de poder acceder en los apuntes y demás elementos de cada asignatura."
                    )
                    await channel.send(embed=embed)
                    return None

        channel = await interaction.user.create_dm()

        embed = nextcord.Embed(
            color=0xc60f33,
            title="Error al verificar.",
            description="No se ha encontrado al usuario indicado" +
            f"\n\nParece ser que **{self.question.value}** no existe. Si crees que se trata de un error, pide ayuda en el Discord."
        )
        await channel.send(embed=embed)
        return None


class Button (nextcord.ui.Button):
    def __init__(self, *, style: ButtonStyle = ButtonStyle.secondary, label: str | None = None, disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | Emoji | PartialEmoji | None = None, row: int | None = None) -> None:
        super().__init__(style=style, label=label, disabled=disabled,
                         custom_id=custom_id, url=url, emoji=emoji, row=row)

    async def callback(self, interaction: Interaction) -> None:
        role_verification = interaction.guild.get_role(1156453646649798726)

        user_role = interaction.user.roles # pyright: ignore[reportGeneralTypeIssues]
        if role_verification in user_role:
            channel = await interaction.user.create_dm()

            embed = nextcord.Embed(
                color=0xc60f33,
                title="Error al verificar.",
                description="Ya tienes la verificación. "
            )
            await channel.send(embed=embed)
            return None
        modal = Modal(title="Verificación de alumno DAW.")
        await interaction.response.send_modal(modal=modal)


class Verifier (commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @nextcord.slash_command(guild_ids=[guild_id], force_global=True,
                            description="Description", default_member_permissions= 8)
    async def verification(self, interaction: Interaction):

        await interaction.response.defer()

        embed = nextcord.Embed(
            title="Verificación de alumnos DAW.",
            description="Si eres un alumno DAW, entonces verifícate para poder acceder a las asignaturas." +
            "\nUsa tu nombre y apellidos completo que aparece en el Campus." +
            "\nCópialo de forma idéntica, incluyendo mayúsculas, como te aparece en el Campus."

        )
        # Create new ui view button
        label = "Verificarse"
        button= Button(label=label)
        view = nextcord.ui.View(timeout= None)
        view.add_item(button)

        message: nextcord.WebhookMessage = await interaction.send(embed=embed, view=view) # pyright: ignore[reportGeneralTypeIssues]

        # save persistent button
        db = Db()

        try:
            db.insert("persistent_views", ["label", "custom_id", "message_id", "channel_id"],
                      [label, button.custom_id, message.id, message.channel.id])
        except BranchWarning:
            pass
# Setup


def setup(bot: commands.Bot):
    # pylint: disable=missing-function-docstring
    bot.add_cog(Verifier(bot))
