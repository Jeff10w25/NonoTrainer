import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_SECRET = os.getenv("TOKEN")
