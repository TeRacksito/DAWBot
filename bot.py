import nextcord
from nextcord.ext import commands

import lib.terminal as terminal
from lib.terminal import error

import os
import sys
import traceback

# Initialize all logging and terminal features.
terminal.initialize()

# Bot Intents definition
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
intents.typing = False
intents.presences = False

# Bot definition
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None, case_insensitive=True)

@bot.event
async def on_ready():
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
    print("---------------------------------------------------------------")

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