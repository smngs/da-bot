import os
from motor import motor_asyncio as motor

DISCORD_API_KEY = os.environ.get("DISCORD_API_KEY")
DISCORD_SERVER_ID = os.environ.get("DISCORD_SERVER_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DATABASE_USER = os.environ.get("DATABASE_USER")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")

dbclient = motor.AsyncIOMotorClient(f"mongodb://{DATABASE_USER}:{DATABASE_PASSWORD}@mongo:27017")
db = dbclient["da-bot"]
