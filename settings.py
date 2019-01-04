# settings.py
#! ./py3env/bin/python3.7

from pathlib import Path  # python3 only
from dotenv import load_dotenv
import os


# OR, explicitly providing path to '.env'
from dotenv import load_dotenv
load_dotenv()

print(SECRET_KEY)
