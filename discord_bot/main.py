import os
import discord
import asyncio
from discord.ext import commands

from utils.config import DISCORD_TOKEN

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


async def load_cogs():
    """Load all cogs from the cogs directory."""
    cog_directory = os.path.join(os.getcwd(), "cogs")
    cogs_loaded = []

    for filename in os.listdir(cog_directory):
        if (
            filename.endswith(".py")
            and filename != "__init__.py"
            and "disabled" not in filename.lower()
        ):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                cogs_loaded.append(cog_name)
            except Exception as e:
                print(f"Failed to load cog {cog_name}: {e}")

    return cogs_loaded


@bot.event
async def on_ready():
    """Event handler when the bot is ready."""
    print(f"Logged in as {bot.user}")
    try:
        # Syncing commands
        sync_commands = await bot.tree.sync()
        print(f"Synced {len(sync_commands)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


async def run_bot():
    """Load cogs and start the bot."""
    try:
        await load_cogs()  # Load cogs asynchronously
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())  # Run the bot using asyncio
    except KeyboardInterrupt:
        print("Keyboard Interrupt detected, exiting...")
