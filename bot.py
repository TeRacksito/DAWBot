import nextcord
from nextcord.ext import commands, ipc

import plib.terminal as terminal
from plib.terminal import error

from plib.persistence import loadPersistentViews
from plib.db_handler import Database as Db

import os
import sys
import json
import traceback

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

        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                self.load_extension(f"cogs.{filename[:-3]}")
                print(terminal.SGR.format(f"Loaded Cogs.{terminal.SGR.apply(filename, terminal.SGR.bold)}",
                                            terminal.SGR.Foreground.rgb(128, 128, 128)))

    async def on_ready(self):
        # load persistent views
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

# Initialize all logging and terminal features.
terminal.initialize()

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
# bot = commands.Bot(command_prefix="!", intents=intents, help_command=None, case_insensitive=True)
bot = DawBot(command_prefix="!", intents=intents, help_command=None, case_insensitive=True)

# @bot.event
# async def on_ready():

#     # load persistent views
#     await loadPersistentViews(bot= bot)
    
#     # pylint: disable=missing-function-docstring
#     await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="/help"))
#     print("---------------------------------------------------------------")
#     # pylint: disable=anomalous-backslash-in-string
#     # pylint: disable=line-too-long
#     logo_asci = "___________         __                  __________        __   \n\_   _____/__  ____/  |_____________    \______   \ _____/  |_ \n |    __)_\  \/  /\   __\_  __ \__  \    |    |  _//  _ \   __|\n |        \>    <  |  |  |  | \// __ \_  |    |   (  <_> )  |  \n/_______  /__/\_ \ |__|  |__|  (____  /  |______  /\____/|__|  \n        \/      \/                  \/          \/             "
#     print(terminal.SGR.format(logo_asci, terminal.SGR.Foreground.cyan), file= sys.__stdout__)
#     print("---------------------------------------------------------------")
#     print(f"The bot's latency is {round(bot.latency * 1000)} ms")
#     print("Logged in as " + str(bot.user))
#     print("---------------------------------------------------------------") # System.out.print()
    

# Cogs loading process.
# if __name__ == "__main__":
#     for filename in os.listdir("cogs"):
#         if filename.endswith(".py"):
#             bot.load_extension(f"cogs.{filename[:-3]}")
#             print(terminal.SGR.format(f"Loaded Cogs.{terminal.SGR.apply(filename, terminal.SGR.bold)}",
#                                       terminal.SGR.Foreground.rgb(128, 128, 128)))


# Attempting to run the bot.
if __name__ == "__main__":
    try:
        bot.ipc.start()
        bot.run(token)
    except Exception as exception: # pylint: disable=broad-exception-caught
        error(exception, traceback.format_exc(),
                    "There was a problem starting the bot",
                    ("Make sure the bot token is loaded correctly.\n"+
                        f"Actual token value type --> ({type(token)}) and value len --> ({len(token)})."),
                        level= "critical")