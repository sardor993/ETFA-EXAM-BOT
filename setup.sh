#!/bin/bash
# PythonAnywhere tezkor setup script

echo "🚀 Telegram Bot tezkor o'rnatish boshlandi..."

# 1. Dependencies o'rnatish
echo "📦 Kutubxonalar o'rnatilmoqda..."
pip3.10 install --user python-telegram-bot==21.7 python-dotenv==1.0.0 flask==3.0.0

# 2. Database yaratish
echo "🗄️ Database yaratilmoqda..."
python3.10 db.py

# 3. Webhook o'rnatish (tokenni o'zingizniki bilan almashtiring)
echo "🔗 Webhook o'rnatilmoqda..."
BOT_TOKEN="8327938988:AAFN5p-C1_x4XPJ3gaBPu5xboqF33NZ0hAw"
USERNAME="yourusername"  # O'zingizning PythonAnywhere username

curl "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook?url=https://${USERNAME}.pythonanywhere.com/webhook"

echo "✅ Setup tugallandi! Web app ni reload qiling."
echo "🤖 Bot manzili: https://${USERNAME}.pythonanywhere.com"