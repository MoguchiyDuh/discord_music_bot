import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GENIUS_TOKEN = os.environ.get("GENIUS_TOKEN")
