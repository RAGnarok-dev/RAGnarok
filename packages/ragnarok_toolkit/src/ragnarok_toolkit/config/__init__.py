import logging
import os

from dotenv import load_dotenv

load_dotenv()

# set logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

ENV = os.environ.get("ENV", "dev")

SERVER_PORT = os.environ.get("SERVER_PORT", "8000")
