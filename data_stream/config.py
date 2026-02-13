import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Config
    """

    POLL_INTERVAL = 3
    DB_PATH = "markets.db"

config = Config()
