@echo off
echo 🤖 Telegram Bot Test Dasturi
echo =============================
echo.
echo 1. Python o'rnatilganligini tekshirish...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python o'rnatilmagan! Python.org dan yuklab oling.
    pause
    exit /b 1
)
echo ✅ Python mavjud

echo.
echo 2. Kutubxonalarni o'rnatish...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Kutubxonalar o'rnatilmadi!
    pause
    exit /b 1
)
echo ✅ Kutubxonalar o'rnatildi

echo.
echo 3. Bot token tekshirish...
findstr /r "BOT_TOKEN=.*[0-9]" .env >nul
if %errorlevel% neq 0 (
    echo ⚠️  Bot token kiritilmagan!
    echo    .env faylini oching va o'z tokeningizni kiriting
    echo    Masalan: BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxyz
    pause
    exit /b 1
)
echo ✅ Bot token mavjud

echo.
echo 4. Botni ishga tushirish...
echo    Bot to'xtatish uchun Ctrl+C bosing
echo.
python bot.py

pause