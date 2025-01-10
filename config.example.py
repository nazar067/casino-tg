#In the root directory, create an config.py file and copy the contents of the config.example.py file there.\
import os
API_TOKEN = "Your telegram bot token"
DATABASE_URL = os.getenv("DATABASE_URL", "connection string to postgress")
