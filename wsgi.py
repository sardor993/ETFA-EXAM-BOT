#!/usr/bin/env python3
"""
WSGI fayl PythonAnywhere uchun - TEZKOR VERSION
Bu faylni WSGI configuration ga to'liq ko'chiring!
"""

import sys
import os

# MUHIM: O'zingizning username va papka nomini kiriting
project_home = '/home/sardor993/telegram_bot'  # Bu yerda o'z ma'lumotlaringizni yozing
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Environment variable (agar .env ishlamasa)
os.environ['BOT_TOKEN'] = '8327938988:AAFN5p-C1_x4XPJ3gaBPu5xboqF33NZ0hAw'

from main import app as application

if __name__ == "__main__":
    application.run()