import os
from dotenv import load_dotenv

load_dotenv()


MONGO_URI=os.getenv("MONGO_URI","mongodb://localhost:27017")
DB_NAME=os.getenv("DB_NAME","attendance_db")
EMBEDDINGS_DIR=os.getenv("EMBEDDINGS_DIR","datasets/embeddings")