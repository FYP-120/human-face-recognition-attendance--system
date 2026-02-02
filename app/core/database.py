from pymongo import MongoClient
from app.core.config import MONGO_URI, DB_NAME


client=MongoClient(MONGO_URI)
db=client[DB_NAME]

def get_collection(collection_name:str):
    return db[collection_name]