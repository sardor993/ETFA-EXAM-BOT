# 🤖 O'zbekiston Test Bot

Bu telegram bot test topshirish uchun mo'ljallangan. Bot 100 ta savoldan tasodifiy 30 tasini tanlab, foydalanuvchiga test taqdim etadi.

## 🚀 Botni o'rnatish va ishga tushirish

### 1. Kerakli dasturlarni o'rnatish

```powershell
# Python o'rnatilganligini tekshiring
python --version

# Pip yordamida kerakli kutubxonalarni o'rnating
pip install -r requirements.txt
```

### 2. Bot Token olish

1. Telegram'da [@BotFather](https://t.me/botfather) botiga o'ting
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting (misol: `Test Quiz Bot`)
4. Bot username kiriting (misol: `my_test_quiz_bot`)
5. BotFather sizga token beradi (misol: `123456789:ABCdefGHIjklMNOpqrSTUvwxyz`)

### 3. Bot sozlash

1. `.env` faylini oching
2. `YOUR_BOT_TOKEN_HERE` o'rniga o'z tokeningizni qo'ying:
   ```
   BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxyz
   ```

### 4. Botni ishga tushirish

```powershell
cd c:\telegram_bot
python bot.py
```

## 📋 Bot imkoniyatlari

### ✨ Asosiy funksiyalar:
- 🎯 100 ta savoldan tasodifiy 30 ta tanlash
- ✅ To'g'ri javoblarni belgilash 
- ❌ Noto'g'ri javoblarni ko'rsatish
- ⬅️ Orqaga qaytish (javobni qayta ko'rish)
- ➡️ Oldinga o'tish
- 🔄 Testni qayta boshlash
- 📊 Natijalarni ko'rsatish

### 🎮 Foydalanish:
1. Botni ishga tushiring
2. Telegram'da botingizni toping
3. `/start` buyrug'ini yuboring
4. Savollarni javoblang
5. Tugmalar yordamida navigatsiya qiling

### 🔧 Tugmalar:
- **A, B, C, D** - Javob variantlari
- **⬅️ Orqaga** - Oldingi savolga qaytish
- **➡️ Oldinga** - Keyingi savolga o'tish  
- **🔄 Qayta boshlash** - Testni boshidan boshlash

## 📁 Fayl tuzilishi

```
telegram_bot/
├── bot.py              # Asosiy bot fayli
├── questions.json      # Test savollari
├── requirements.txt    # Python kutubxonalari
├── .env               # Bot sozlamalari
└── README.md          # Bu fayl
```

## 🛠 Sozlamalar

### Savollar soni o'zgartirish:
`bot.py` faylida `start_new_quiz` funksiyasida `30` ni boshqa raqamga o'zgartiring.

### Yangi savollar qo'shish:
`questions.json` faylida yangi savollar qo'shing. Har bir savol quyidagi formatda bo'lishi kerak:

```json
{
  "id": 101,
  "question": "Savol matni?",
  "options": ["A variant", "B variant", "C variant", "D variant"],
  "correct_answer": "A"
}
```

### ⚠️ Muhim eslatmalar:

1. **Bot Token** ni hech kimga bermang!
2. `.env` faylini git'ga yuklmang
3. Botni to'xtatish uchun `Ctrl+C` bosing
4. Server yoki kompyuteringiz o'chiq bo'lsa, bot ishlamaydi

### 🆘 Muammolar hal qilish:

**Bot javob bermayapti:**
- Token to'g'ri kiritilganligini tekshiring
- Internet ulanishini tekshiring
- `python bot.py` buyrug'ini qayta ishga tushiring

**Savollar yuklanmayapti:**
- `questions.json` fayli mavjudligini tekshiring
- JSON format to'g'riligini tekshiring

**Kutubxona xatolari:**
- `pip install -r requirements.txt` buyrug'ini qayta bajaring
- Python versiyasini tekshiring (3.7+)

## 📞 Yordam

Agar savollaringiz bo'lsa yoki yordam kerak bo'lsa, README.md faylini o'qing yoki Python/Telegram bot hujjatlarni ko'ring.

Muvaffaqiyat tilaymiz! 🎉