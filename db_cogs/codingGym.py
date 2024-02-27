import datetime
from io import BytesIO
import re
import time
from typing import Optional
import zipfile
from discord import DMChannel
import nextcord
import os
import platform
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, tasks, ipc, application_checks
from nextcord.ext.application_checks import ApplicationPrivateMessageOnly
import shutil
from bot import DawBot

from plib.PriorityQueue import PriorityQueue

guild_id = int(os.environ["guild_id"])

from plib.db_handler import Database as Db

db = Db()

DIFFICULTY = {
    "Fácil": 1,
    "Medio": 2,
    "Difícil": 3
}

REVERSE_DIFFICULTY = {v: k for k, v in DIFFICULTY.items()}

EX_TYPES = {
    "ejercicio semanal": "WEEK_EXERCISE",
    "ejercicio diario": "DAILY_EXERCISE",
    "ejercicio de práctica": "PRACTICE_EXERCISE",
    "ejercicio específico": "SPECIFIC_EXERCISE"
}

REVERSE_EX_TYPES = {v: k for k, v in EX_TYPES.items()}

EMBED_COLORS = {
    "WEEK_EXERCISE": [nextcord.Color.gold(), nextcord.Color.dark_gold()],
    "DAILY_EXERCISE": [nextcord.Color.teal(), nextcord.Color.dark_teal()],
    "PRACTICE_EXERCISE": [nextcord.Color.blue(), nextcord.Color.dark_blue()],
    "SPECIFIC_EXERCISE": [nextcord.Color.magenta(), nextcord.Color.dark_magenta()]
}
class View(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.category = None
        self.index = 0
        self.last_useful_index = None
        self.previous.disabled = True
        self.next.disabled = True
        self.cache = {}
    
    async def update(self, interaction: Interaction):
        try:
            exercises = self.cache[self.index]
        except KeyError:
            exercises = db.query(f"SELECT id, title, description FROM EXERCISE WHERE type LIKE '{EX_TYPES[self.category]}' ORDER BY timestamp DESC LIMIT 10 OFFSET {self.index * 10};")
            self.cache[self.index] = exercises
        
        result = str()

        if not exercises:
            self.next.disabled = True
            if self.last_useful_index is not None:
                self.index = self.last_useful_index + 1                
            self.last_useful_index = -1 if self.index == 0 else self.index - 1
            result = "No hay ejercicios para mostrar." if self.index == 0 else "No hay más ejercicios para mostrar."     

        for exercise in exercises:
            result += (
                f"**{exercise[1]}**\n"
                f"ID: **{exercise[0]}**\n"
                f"Descripción: {exercise[2]}\n\n")
        
        embed = nextcord.Embed(title= f"Ejercicios de {self.category.capitalize()}", description= result, color= EMBED_COLORS[EX_TYPES[self.category]][0])
        embed.set_footer(text= f"Página {self.index + 1}")
        await interaction.response.edit_message(embed= embed, view= self)
        
    @nextcord.ui.button(label= "Anterior", style= nextcord.ButtonStyle.secondary)
    async def previous(self, button: nextcord.ui.Button, interaction: Interaction):
        self.index -= 1
        if self.index == 0:
            self.previous.disabled = True
        if self.last_useful_index is None or self.index < self.last_useful_index:
                self.next.disabled = False
        await self.update(interaction)

    @nextcord.ui.button(label= "Siguiente", style= nextcord.ButtonStyle.secondary)
    async def next(self, button: nextcord.ui.Button, interaction: Interaction):
        self.index += 1
        if self.index > 0:
            self.previous.disabled = False
        await self.update(interaction)

    @nextcord.ui.select(placeholder= "Selecciona una opción...", options= [nextcord.SelectOption(label= value.capitalize(), value= value) for value in EX_TYPES.keys()])
    async def select(self, select: nextcord.ui.Select, interaction: Interaction):
        self.next.disabled = False
        self.cache.clear()
        self.category = select.values[0]
        self.index = 0
        await self.update(interaction)

class CodingGym(commands.Cog):
    
    def __init__(self, bot: DawBot) -> None:
        self.bot = bot
        self.queue = PriorityQueue()
        self.weekly_schedule.start()
        self.daily_schedule.start()
    
    async def isdaw_member(self, interaction: Interaction):
        user = interaction.user
        guild: nextcord.Guild = await self.bot.fetch_guild(guild_id)
        member = guild.get_member(user.id)
        if not member:
            return False
        
        member_role_id = int(db.select("BASIC_INFO", {"name": "member_role_id"})[0][1]) # type: ignore
        
        member_role = member.get_role(member_role_id)

        if not member_role:
            return False        

        return True

    async def iddaw_admin(self, interaction: Interaction):
        user = interaction.user
        guild: nextcord.Guild = await self.bot.fetch_guild(guild_id)
        member = guild.get_member(user.id)
        if not member:
            return False
        
        admin_role_id = int(db.select("BASIC_INFO", {"name": "admin_role_id"})[0][1]) # type: ignore

        admin_role = member.get_role(admin_role_id)

        if not admin_role:
            return False
        
        return True

    @staticmethod
    def generateTempPath(message):
        if (platform.system() == "Windows"):
            path = os.path.join(os.environ["TEMP"], "DawBotcodingGym")
        
        elif (platform.system() == "Linux"):
            path = os.path.join("/tmp", "DawBotcodingGym")
        else:
            raise Exception("Unsupported OS")

        if not os.path.exists(path):
            os.makedirs(path)
        
        path = os.path.join(path, f"{message.id}")
        n = 0

        if not os.path.exists(path):
            os.makedirs(path)
        else:
            while True:
                n += 1
                temp_path = path + f"_{n}"
                if not os.path.exists(temp_path):
                    os.makedirs(temp_path)
                    path = temp_path
                    break
        return path

    @staticmethod
    def extract_class_and_main(java_code: str):
        class_match = re.search(r'class\s+(\w+)', java_code)
        if class_match:
            class_name = class_match.group(1)
        else:
            return None

        main_method_match = re.search(r'public\s+static\s+void\s+main\s*\(', java_code)
        if main_method_match:
            return class_name
        else:
            return None
    
    @staticmethod
    def show_exercise(exercise: tuple):
        embeds: list[nextcord.Embed] = []
        file = None

        colors = EMBED_COLORS[exercise[1]]

        embeds.append(nextcord.Embed(title= f"Ejercicio `{exercise[2]}`", description= exercise[3], color= colors[0]))
        embeds.append(nextcord.Embed(
            title= "Información",
            description= (
                f"ID: {exercise[0]}\n"
                f"Categoría: {REVERSE_EX_TYPES[exercise[1]].capitalize()}\n"
                f"Dificultad: {REVERSE_DIFFICULTY[exercise[4]]}\n"
            ),
            color= colors[1]
        ))
        if exercise[5]:
            embeds.append(nextcord.Embed(
                title= "Contenido",
                description= exercise[5],
                color= colors[1]
            ))
        else:
            zip_data = exercise[6]

            zip_buffer = BytesIO(zip_data)

            with zipfile.ZipFile(zip_buffer, "r") as zip_ref:                
                for file_name in zip_ref.namelist():
                    if file_name.startswith("content_") and file_name.endswith(".java"):
                        file = nextcord.File(BytesIO(zip_ref.read(file_name)), filename= "Main.java")
        

        return (embeds, file)
    
    
    @tasks.loop(time= datetime.time(hour= 8, minute=0))
    async def weekly_schedule(self):
        try:
        
            now = datetime.datetime.now()

            if not now.weekday() == 3:
                return

            exercise_id = db.query("SELECT id FROM WEEKLY_SCHEDULE ORDER BY priority, timestamp ASC LIMIT 1;")
            last_ex = db.query("SELECT * FROM WEEKLY_SCHEDULE_LAST;")

            if last_ex:
                last_time: datetime.datetime = last_ex[0][1] # type: ignore

                if last_time.date() == now.date():
                    return


            if not exercise_id:
                return
            
            exercise_id = exercise_id[0][0]

            exercise = db.select("EXERCISE", {"id": exercise_id})[0]

            channel_id = int(db.select("BASIC_INFO", {"name": "week_ex_channel"})[0][1]) # type: ignore

            channel: nextcord.TextChannel = await self.bot.fetch_channel(channel_id)

            if not channel:
                print("No se encontró el canal especificado.")
                return
            
            embeds, file = self.show_exercise(exercise)
        
            if file:
                await channel.send("@everyone", embeds= embeds, file= file)
            else:
                await channel.send("@everyone", embeds= embeds)
            
            db.delete("WEEKLY_SCHEDULE", {"id": exercise_id})
            db.query("DELETE FROM WEEKLY_SCHEDULE_LAST;")
            db.insert("WEEKLY_SCHEDULE_LAST", ["id"], [exercise_id])

            
        except Exception as e:
            print(e)
            return

    @weekly_schedule.before_loop
    async def weekly_schedule_wait(self):
        await self.bot.wait_until_ready()
    

    @tasks.loop(time= [datetime.time(hour= 8, minute=0), datetime.time(hour= 18, minute=40)])
    async def daily_schedule(self):
        try:
        
            now = datetime.datetime.now()

            exercise_id = db.query("SELECT id FROM DAILY_SCHEDULE ORDER BY priority, timestamp ASC LIMIT 1;")
            last_ex = db.query("SELECT * FROM DAILY_SCHEDULE_LAST;")

            if last_ex:
                last_time: datetime.datetime = last_ex[0][1] # type: ignore

                if last_time.date() == now.date():
                    if now.hour - last_time.hour < 9:
                        return

            if not exercise_id:
                return
            
            exercise_id = exercise_id[0][0]

            exercise = db.select("EXERCISE", {"id": exercise_id})[0]

            channel_id = int(db.select("BASIC_INFO", {"name": "day_ex_channel"})[0][1]) # type: ignore

            channel: nextcord.TextChannel = await self.bot.fetch_channel(channel_id)

            if not channel:
                print("No se encontró el canal especificado.")
                return
            
            embeds, file = self.show_exercise(exercise)
        
            if file:
                await channel.send("@everyone", embeds= embeds, file= file)
            else:
                await channel.send("@everyone", embeds= embeds)
            
            db.delete("DAILY_SCHEDULE", {"id": exercise_id})
            db.query("DELETE FROM DAILY_SCHEDULE_LAST;")
            db.insert("DAILY_SCHEDULE_LAST", ["id"], [exercise_id])

        
        except Exception as e:
            print(e)
            return

    @daily_schedule.before_loop
    async def daily_schedule_wait(self):
        await self.bot.wait_until_ready()

    
    @nextcord.slash_command(guild_ids=[guild_id], force_global=True,
                            name="programar",
                            description="Description")
    async def schedule(self, interaction: Interaction):
        pass

    @schedule.subcommand(name="ejercicio", description="Programar ejercicios.")
    async def sc_exercise(self, interaction: Interaction):
        pass

    @sc_exercise.subcommand(name="ahora", description="Programa un ejercicio ahora.")
    async def schedule_now(self, interaction: Interaction,
                            id: int = SlashOption(name= "id", description= "ID del ejercicio.", required= True)):
        await interaction.response.defer(ephemeral= True)

        if not await self.iddaw_admin(interaction):
            await interaction.send("Debes ser administrador DAW verificado para usar este comando.", ephemeral= True)
            return

        exercise = db.select("EXERCISE", {"id": id})

        if not exercise:
            await interaction.send("No se encontró el ejercicio especificado.", ephemeral= True)
            return
        
        exercise = exercise[0]

        channel_id = int(db.select("BASIC_INFO", {"name": "now_ex_channel"})[0][1]) # type: ignore

        channel: nextcord.TextChannel = await self.bot.fetch_channel(channel_id)

        if not channel:
            await interaction.send("No se encontró el canal especificado.", ephemeral= True)
            return
        
        embeds, file = self.show_exercise(exercise)

        if file:
            await channel.send("@everyone", embeds= embeds, file= file)
        else:
            await channel.send("@everyone", embeds= embeds)
    
    @sc_exercise.subcommand(name="semanal", description="Programa un ejercicio semanal.")
    async def schedule_weekly(self, interaction: Interaction,
                            id: int = SlashOption(name= "id", description= "ID del ejercicio.", required= True),
                            priority: int = SlashOption(name= "prioridad", description= "Prioridad del ejercicio.", required= False, default= 5)):
        
        await interaction.response.defer(ephemeral= True)

        if not await self.iddaw_admin(interaction):
            await interaction.send("Debes ser administrador DAW verificado para usar este comando.", ephemeral= True)
            return

        exercise = db.select("EXERCISE", {"id": id})

        if not exercise:
            await interaction.send("No se encontró el ejercicio especificado.", ephemeral= True)
            return
        
        exercise = exercise[0]

        db.insert("WEEKLY_SCHEDULE", ["id", "priority"], [id, priority])

        await interaction.send(f"¡Ejercicio `{exercise[2]}` programado satisfactoriamente!", ephemeral= True)

    @sc_exercise.subcommand(name="diario", description="Programa un ejercicio diario.")
    async def schedule_daily(self, interaction: Interaction,
                            id: int = SlashOption(name= "id", description= "ID del ejercicio.", required= True),
                            priority: int = SlashOption(name= "prioridad", description= "Prioridad del ejercicio.", required= False, default= 5)):
        
        await interaction.response.defer(ephemeral= True)

        if not await self.iddaw_admin(interaction):
            await interaction.send("Debes ser administrador DAW verificado para usar este comando.", ephemeral= True)
            return

        exercise = db.select("EXERCISE", {"id": id})

        if not exercise:
            await interaction.send("No se encontró el ejercicio especificado.", ephemeral= True)
            return

        exercise = exercise[0]
        
        db.insert("DAILY_SCHEDULE", ["id", "priority"], [id, priority])

        await interaction.send(f"¡Ejercicio `{exercise[2]}` programado satisfactoriamente!", ephemeral= True)

    @nextcord.slash_command(guild_ids=[guild_id], force_global=True,
                            name="crear",
                            description="Description")
    async def create(self, interaction: Interaction):
        pass

    @create.subcommand(name="ejercicio", description="Crea un ejercicio nuevo.")
    async def create_ex(self, interaction: Interaction,
                       title: str = SlashOption(name= "título", description= "Título del ejercicio.", required= True),
                       description: str = SlashOption(name= "descripción", description= "Descripción del ejercicio.", required= True),
                       category: str = SlashOption(name= "categoría", description= "Categoría a la que pertenece.", required= True, choices= [
                              "Ejercicio semanal",
                              "Ejercicio diario",
                              "Ejercicio de práctica",
                              "Ejercicio específico"
                              ]),
                       url: str = SlashOption(name= "url", description= "URL al mensaje con el contenido.", required= True),
                       difficulty: str = SlashOption(name= "dificultad", description= "Dificultad del ejercicio.", required= True, choices= [
                              "Fácil",
                              "Medio",
                              "Difícil"
                              ]),
                       ):

        await interaction.response.defer(ephemeral= True)

        if not await self.iddaw_admin(interaction):
            await interaction.send("Debes ser administrador DAW verificado para usar este comando.", ephemeral= True)
            return

        category = EX_TYPES[category.lower()]

        if ("/" in url):
            url = url.split("/")[-1]

        message: nextcord.Message = await interaction.channel.fetch_message(int(url))

        files = message.attachments
        
        # create temp folder, download files, zip them, send them, delete temp folder

        path = self.generateTempPath(message)

        if not files:
            if not message.content:
                await interaction.send("No hay contenido que ejecutar.", ephemeral= True)
                return
            
            content = message.content

            if not content.startswith("```java") and not content.endswith("```"):
                await interaction.send((
                    "El contenido del mensaje no está correctamente formateado.\n"
                    "Se espera que el contenido esté vacío (si se adjuntan archivos) o entre bloques de código (Si no hay archivos adjuntos).\n"
                    "Por favor, asegúrate de que el contenido esté entre bloques de código."
                    "Por ejemplo:\n"
                    "```java\n"
                    "public class Main {\n"
                    "    public static void main(String[] args) {\n"
                    "        System.out.println(\"Hello, World!\");\n"
                    "    }\n"
                    "}\n"
                    "```"
                ), ephemeral= True)
                return

            if self.extract_class_and_main(content) is None:
                await interaction.send("No se encontró una clase principal en el contenido.", ephemeral= True)
                return
        
        for file in files:
            await file.save(os.path.join(path, file.filename))
        
        # zip files

        shutil.make_archive(path, "zip", path)

        # save payload

        with open(f"{path}.zip", "rb") as f:
            data = f.read()

        id = db.insert("EXERCISE",
                       ["type", "title", "description", "difficulty", "content", "file"],
                       [category, title, description, DIFFICULTY[difficulty], message.content, data],
                       retrieve_id= True)

        embed1 = nextcord.Embed(title= f"El ejercicio {title} ha sido creado satisfactoriamente.",
                                description= (
                                    f"Descripción: **{description}**\n" +
                                    f"Categoría: **{category}**\n" +
                                    f"Dificultad: **{difficulty}**\n" +
                                    f"ID: **{id}**\n"
                                ), color= nextcord.Color.blue())
        embed2 = nextcord.Embed(title= "Contenido", description= message.content if message.content else "No hay contenido en bruto.", color= nextcord.Color.blue())

        embed3 = nextcord.Embed(title= "Archivos adjuntos",
                                description= "\n".join([f"[{file.filename}]({file.url})" for file in files]) if files else "No hay archivos adjuntos.",
                                color= nextcord.Color.blue())

        await interaction.send(embeds= [embed1, embed2, embed3], ephemeral= True)

        # clear temp folder
        time.sleep(1)
        shutil.rmtree(path)


    
    @nextcord.slash_command(guild_ids=[guild_id], force_global=True,
                        name="resolver",
                        description="Resolver un ejercicio o test.")
    async def solve(self, interaction: Interaction):
        pass
    

    
        pass
    @solve.subcommand(name="ejercicio", description="Resolver un ejercicio.")
    @application_checks.dm_only()
    async def solve_ex(self, interaction: Interaction,
                    category: str = SlashOption(name= "categoría", description= "Categoría a la que pertenece.", required= True, choices= [
                              "Ejercicio semanal",
                              "Ejercicio diario",
                              "Ejercicio de práctica",
                              "Ejercicio específico"
                              ]),
                    id: int = SlashOption(name= "id", description= "ID del ejercicio.", required= True),
                    url: str = SlashOption(name= "url", description= "ID o URL al mensaje con el contenido.", required= True)):

        await interaction.response.defer(ephemeral= True)

        if not await self.isdaw_member(interaction):
            await interaction.send("Debes ser miembro DAW verificado para usar este comando.", ephemeral= True)
            return

        category = EX_TYPES[category.lower()]
        
        if ("/" in url):
            url = url.split("/")[-1]
        
        exercise = db.select("EXERCISE", {"id": id, "type": category})

        if not exercise:
            await interaction.send("No se encontró el ejercicio especificado.", ephemeral= True)
            return
        
        try:
            message: nextcord.Message = await interaction.channel.fetch_message(int(url))
        except nextcord.errors.NotFound:
            await interaction.send("No se encontró el mensaje especificado.", ephemeral= True)
            return

        files = message.attachments

        path = self.generateTempPath(message)

        user_path = os.path.join(path, str(interaction.user.id))

        if not os.path.exists(user_path):
            os.makedirs(user_path)

        if not files:
            if not message.content:
                await interaction.send("No hay contenido que ejecutar.", ephemeral= True)
                return
            
            content = message.content

            if not content.startswith("```java") and not content.endswith("```"):
                await interaction.send((
                    "El contenido del mensaje no está correctamente formateado.\n"
                    "Se espera que el contenido esté vacío (si se adjuntan archivos) o entre bloques de código (Si no hay archivos adjuntos).\n"
                    "Por favor, asegúrate de que el contenido esté entre bloques de código."
                    "Por ejemplo:\n"
                    "```java\n"
                    "public class Main {\n"
                    "    public static void main(String[] args) {\n"
                    "        System.out.println(\"Hello, World!\");\n"
                    "    }\n"
                    "}\n"
                    "```"
                ), ephemeral= True)
                return
            
            content = content.removeprefix("```java").removesuffix("```")
            
            main_name = self.extract_class_and_main(content)

            if main_name is None:
                await interaction.send("No se encontró una clase principal en el contenido.", ephemeral= True)
                return
            
            with open(os.path.join(user_path, f"{main_name}.java"), "w", encoding="utf-8") as f:
                f.write(content)
            
        for file in files:
            if file.filename.endswith(".zip"):
                await file.save(os.path.join(user_path, file.filename))
                shutil.unpack_archive(os.path.join(user_path, file.filename), user_path)
                os.remove(os.path.join(user_path, file.filename))
                continue
            await file.save(os.path.join(user_path, file.filename))

        attempts = 0

        while attempts < 3:

            conn = self.bot.getConnection()
            
            try:                
                self.bot.conn.send({
                    "id_exec": id,
                    "id_user": interaction.user.id,
                    "path": path,
                    "category": category,
                    "step": 0,
                    "priority": 5
                })
                break
            except (ConnectionResetError, ConnectionAbortedError, AttributeError):
                self.bot.conn = None
                attempts += 1
        if attempts >= 3:
            await interaction.send("Parece ser que el servidor de ejercicios no está disponible en este momento. Inténtalo de nuevo.", ephemeral= True)
            return
        await interaction.send("¡El ejercicio ha sido enviado a la cola de revisión!\nEsto puede tardar varios minutos...", ephemeral= True)

    @solve_ex.error # type: ignore
    async def solve_ex_error(self, interaction: Interaction, error: nextcord.ApplicationError):
        if isinstance(error, ApplicationPrivateMessageOnly):
            await interaction.send("Este comando solo puede ser usado en mensajes privados.", ephemeral= True)
        

    @nextcord.slash_command(guild_ids=[guild_id], force_global=True,
                            name="ver",
                            description="Ver un ejercicio o test.")
    async def see(self, interaction: Interaction):
        pass

    @see.subcommand(name="ejercicio", description="Ver un ejercicio específico.")
    @application_checks.dm_only()
    async def see_ex(self, interaction: Interaction,
                    category: str = SlashOption(name= "categoría", description= "Categoría a la que pertenece.", required= True, choices= [
                              "Ejercicio semanal",
                              "Ejercicio diario",
                              "Ejercicio de práctica",
                              "Ejercicio específico"
                              ]),
                    id: int = SlashOption(name= "id", description= "ID del ejercicio.", required= True)):
        
        await interaction.response.defer(ephemeral= True)

        category = EX_TYPES[category.lower()]

        exercise = db.select("EXERCISE", {"id": id, "type": category})

        if not exercise:
            await interaction.send("No se encontró el ejercicio especificado.", ephemeral= True)
            return
        
        exercise = exercise[0]

        embeds, file = self.show_exercise(exercise)
        
        if file:
            await interaction.send(embeds= embeds, file= file, ephemeral= True)
        else:
            await interaction.send(embeds= embeds, ephemeral= True)

    @see_ex.error # type: ignore
    async def see_ex_error(self, interaction: Interaction, error: nextcord.ApplicationError):
        if isinstance(error, ApplicationPrivateMessageOnly):
            await interaction.send("Este comando solo puede ser usado en mensajes privados.", ephemeral= True)
    
    @see.subcommand(name="lista", description="Ver una lista de ejercicios o tests.")
    async def see_list(self, interaction: Interaction):
        pass

    @see_list.subcommand(name="ejercicios", description="Ver una lista de ejercicios.")
    @application_checks.dm_only()
    async def see_list_ex(self, interaction: Interaction):
        
        view = View()
        embed = nextcord.Embed(title= f"Lista de ejercicios.", description= "_Utiliza los botones para navegar_", color= nextcord.Color.blue())
        await interaction.response.send_message(ephemeral= True, view= view, embed= embed)

    @ipc.server.route()
    async def status(self, _):
        return 200

    @ipc.server.route()
    async def update(self):
        return self.queue.clear()
    
    @ipc.server.route()
    async def terminateJob(self, payload):

        data = payload.data

        category = REVERSE_EX_TYPES[data["category"]]
        
        user: nextcord.User = await self.bot.fetch_user(data["id_user"])

        exercise = db.select("EXERCISE", {"id": data["id_exec"], "type": data["category"]}, ["title"])[0]

        dm: DMChannel = await user.create_dm()

        embeds = []

        if data["broken"]:
            embeds.append(nextcord.Embed(title= "Hubo un problema...",
                                    description= (
                                        f"Corrección del ejercicio `{exercise[0]}`.\n"
                                        f"Parece ser que hubo un problema al corregir el ejercicio.\n"
                                    ),
                                    color= nextcord.Color.red()))
        else:
            embeds.append(nextcord.Embed(title= "Corrección completada",
                                    description= (
                                        f"Corrección del ejercicio `{exercise[0]}`.\n"
                                        f"La corrección ha sido completada satisfactoriamente.\n"
                                    ),
                                    color= nextcord.Color.green()))
        
        embeds.append(nextcord.Embed(
            title= "Información",
            description= (
                f"ID del ejercicio: {data['id_exec']}\n"
                f"Tipo de proyecto detectado: {data['project_type']}\n"
                f"Categoría: {category}\n"
                f"Estado: {'Correcto' if not data['broken'] else 'Incorrecto'}\n"
                f"Variación abstracta: {data['abstraction_score'] if data['abstraction_score'] is not None else 'Improcedente'}\n"
                f"{('Estructuras prohibidas usadas: ' if data['banned_found'] else 'No se detectaron estructuras prohibidas.') if data['abstraction_score'] is not None else ''}" + (''.join([f"\n- `{value}`" for value in data['banned_found']]) if data['banned_found'] else '')
            ),
            color= nextcord.Color.blue()
        ))
        
        embeds.append(nextcord.Embed(
            title= "Resultado de la corrección",
            description= data["text_content"],
            color= nextcord.Color.blue()
        ))

        if data["gpt_content"]:
            embeds.append(nextcord.Embed(
                title= "ChatGPT",
                description= data["gpt_content"],
                color= nextcord.Color.blue()
            ))

        await dm.send(embeds= embeds)

        return True

def setup(bot: DawBot):
    bot.add_cog(CodingGym(bot))
