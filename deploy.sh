#!/bin/bash

# 1. Git repository yaratish
echo "🔄 Git repository tayyorlanmoqda..."

# Git repository boshlash
git init

# Barcha fayllarni qo'shish
git add .

# Commit yaratish
git commit -m "Initial commit: Telegram Quiz Bot with all features"

# GitHub remote qo'shish (bu yerga o'zingizning repository URL ni qo'ying)
# git remote add origin https://github.com/SIZNING_USERNAME/telegram-quiz-bot.git

# GitHub ga push qilish
# git branch -M main
# git push -u origin main

echo "✅ Git repository tayyor!"
echo ""
echo "📋 Keyingi qadamlar:"
echo "1. GitHub da yangi repository yarating"
echo "2. git remote add origin <SIZNING_REPO_URL>"
echo "3. git branch -M main"
echo "4. git push -u origin main"
echo "5. Railway.app yoki Render.com ga boring"
echo "6. GitHub repository connect qiling"
echo "7. BOT_TOKEN environment variable qo'shing"
echo "8. Deploy qiling!"