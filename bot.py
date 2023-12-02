import plib.terminal as terminal

# Initialize all logging and terminal features.
terminal.initialize()

from plib.terminal import error
from plib.db_handler import Database as Db
import os
import sys
import json
import traceback

try:
    CONNECTION_TEST = Db()
except Exception as e: # pylint: disable=broad-exception-caught
    error(e, traceback.format_exc(),
        "There was a problem connecting to the database, not loading database dependent cogs.",
        "Make sure the database credentials are loaded correctly.",
            level= "WARNING")
    CONNECTION_TEST = None

if CONNECTION_TEST is not None:
    os.environ["guild_id"] = str(int(CONNECTION_TEST.select("BASIC_INFO", {"name": "guild_id"})[0][1]))
else:
    os.environ["guild_id"] = "1156345547788136539"

import nextcord
from nextcord.ext import commands, ipc
from plib.persistence import loadPersistentViews

def loadCogs(bot: commands.Bot, path: str = "cogs"):
    """
    Loads all cogs from a given path.

    Parameters
    ----------
    bot : `commands.Bot`
        Bot object.
    path : `str`, optional
        Path to load cogs from, by default "cogs"
    """
    for filename in os.listdir(path):
        if filename.endswith(".py"):
            bot.load_extension(f"{path}.{filename[:-3]}")
            print(terminal.SGR.format(f"Loaded {path}.{terminal.SGR.apply(filename, terminal.SGR.bold)}",
                                        terminal.SGR.Foreground.rgb(128, 128, 128)))

class DawBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if ipc_key is not None:
            self.ipc = ipc.server.Server(self, secret_key=ipc_key)
        else:
            self.ipc = None
            print("---------------------------------------------------------------")
            print("IPC Server will not be started due to the lack of an IPC key.")
            print("---------------------------------------------------------------")

        loadCogs(self)

        if CONNECTION_TEST is not None:
            loadCogs(self, "db_cogs")

    async def on_ready(self):
        # load persistent views
        if CONNECTION_TEST is not None:
            await loadPersistentViews(bot= self)
        
        # pylint: disable=missing-function-docstring
        await self.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="/help"))
        print("---------------------------------------------------------------")
        # pylint: disable=anomalous-backslash-in-string
        # pylint: disable=line-too-long
        logo_asci = "___________         __                  __________        __   \n\_   _____/__  ____/  |_____________    \______   \ _____/  |_ \n |    __)_\  \/  /\   __\_  __ \__  \    |    |  _//  _ \   __|\n |        \>    <  |  |  |  | \// __ \_  |    |   (  <_> )  |  \n/_______  /__/\_ \ |__|  |__|  (____  /  |______  /\____/|__|  \n        \/      \/                  \/          \/             "
        print(terminal.SGR.format(logo_asci, terminal.SGR.Foreground.cyan), file= sys.__stdout__)
        print("---------------------------------------------------------------")
        print(f"The bot's latency is {round(self.latency * 1000)} ms")
        print("Logged in as " + str(self.user))
        print("---------------------------------------------------------------") # System.out.print()
    
    async def on_ipc_ready(self):
        print("---------------------------------------------------------------")
        print("IPC Server is ready!")
        print("---------------------------------------------------------------")

    async def on_ipc_error(self, endpoint, error):
        print(endpoint, "raised", error)



with open("TOKEN.json") as file:
    data = json.load(file)
    token = data["token"]
    try:
        ipc_key = data["ipc_key"]
    except KeyError:
        ipc_key = None

# Bot Intents definition
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
intents.typing = False
intents.presences = False
intents.all

# Bot definition
bot = DawBot(command_prefix="!", intents=intents, help_command=None, case_insensitive=True)

# Attempting to run the bot.
if __name__ == "__main__":
    try:
        if bot.ipc is not None:
            bot.ipc.start()
        bot.run(token)
    except Exception as exception: # pylint: disable=broad-exception-caught
        error(exception, traceback.format_exc(),
                    "There was a problem starting the bot",
                    ("Make sure the bot token is loaded correctly.\n"+
                        f"Actual token value type --> ({type(token)}) and value len --> ({len(token)})."),
                        level= "critical")
