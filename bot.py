import nextcord
from nextcord.ext import commands

import plib.terminal as terminal
from plib.terminal import error

from plib.persistence import loadPersistentViews
from plib.db_handler import Database as Db

import os
import sys
import json
import traceback

# Initialize all logging and terminal features.
terminal.initialize()

with open("TOKEN.json") as file:
    data = json.load(file)
    token = data["token"]

# Bot Intents definition
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
intents.typing = False
intents.presences = False
intents.all

# Bot definition
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None, case_insensitive=True)

@bot.event
async def on_ready():

    # load persistent views
    await loadPersistentViews(bot= bot)
        
    # button = Button(label= "test", custom_id= "88d66f6dfca384b76c7e5a04dff86461")
    # view = nextcord.ui.View()
    # view.add_item(button)

    #CHANGE

    # bot.add_view(view= view)

    # pylint: disable=missing-function-docstring
    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="/help"))
    print("---------------------------------------------------------------")
    # pylint: disable=anomalous-backslash-in-string
    # pylint: disable=line-too-long
    logo_asci = "___________         __                  __________        __   \n\_   _____/__  ____/  |_____________    \______   \ _____/  |_ \n |    __)_\  \/  /\   __\_  __ \__  \    |    |  _//  _ \   __|\n |        \>    <  |  |  |  | \// __ \_  |    |   (  <_> )  |  \n/_______  /__/\_ \ |__|  |__|  (____  /  |______  /\____/|__|  \n        \/      \/                  \/          \/             "
    print(terminal.SGR.format(logo_asci, terminal.SGR.Foreground.cyan), file= sys.__stdout__)
    print("---------------------------------------------------------------")
    print(f"The bot's latency is {round(bot.latency * 1000)} ms")
    print("Logged in as " + str(bot.user))
    print("---------------------------------------------------------------") # System.out.print()
    

# Cogs loading process.
if __name__ == "__main__":
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(terminal.SGR.format(f"Loaded Cogs.{terminal.SGR.apply(filename, terminal.SGR.bold)}",
                                      terminal.SGR.Foreground.rgb(128, 128, 128)))


    # Attempting to run the bot.
    try:
        bot.run(token)
    except Exception as exception: # pylint: disable=broad-exception-caught
        error(exception, traceback.format_exc(),
                    "There was a problem starting the bot",
                    ("Make sure the bot token is loaded correctly.\n"+
                        f"Actual token value type --> ({type(token)}) and value len --> ({len(token)})."),
                        level= "critical")