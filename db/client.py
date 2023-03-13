from config.db import DATABASE_USER, DATABASE_PASSWORD
from motor import motor_asyncio as motor

dbclient = motor.AsyncIOMotorClient(f"mongodb://{DATABASE_USER}:{DATABASE_PASSWORD}@mongo:27017")
db = dbclient["da-bot"]
