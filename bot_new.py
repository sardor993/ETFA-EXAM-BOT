import logging
import json
import random
import os
from datetime import datetime
from typing import Dict, Any
import db
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# .env fayldan o'zgaruvchilarni yuklash
load_dotenv()

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token - .env fayldan olish
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

class MultiLanguageQuizBot:
    def __init__(self):
        self.questions = {}
        self.translations = {}
        self.user_sessions = {}  # Har bir user uchun sessiya ma'lumotlari
        self.user_stats = []  # Foydalanuvchilar statistikasi
        # Initialize DB and load data
        db.init_db()
        self.load_data()
        self.load_stats()
    
    def load_stats(self):
        """Statistika ma'lumotlarini yuklash"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            stats_path = os.path.join(current_dir, 'user_stats.json')
            with open(stats_path, 'r', encoding='utf-8') as f:
                self.user_stats = json.load(f)
        except FileNotFoundError:
            self.user_stats = []
    
    def save_stats(self):
        """Statistika ma'lumotlarini saqlash"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            stats_path = os.path.join(current_dir, 'user_stats.json')
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Statistika saqlashda xatolik: {e}")
    
    def log_user_activity(self, user_id: int, username: str, first_name: str, activity: str, subject: str = None):
        """Foydalanuvchi faoliyatini loglash"""
        activity_log = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'activity': activity,
            'subject': subject,
            'timestamp': datetime.now().isoformat()
        }
        self.user_stats.append(activity_log)
        self.save_stats()
    
    def get_stats_summary(self):
        """Umumiy statistika ma'lumotlari"""
        if not self.user_stats:
            return "📊 Hozircha statistika ma'lumotlari yo'q"
        
        unique_users = len(set(log['user_id'] for log in self.user_stats))
        total_tests = len([log for log in self.user_stats if log['activity'] == 'test_started'])
        completed_tests = len([log for log in self.user_stats if log['activity'] == 'test_completed'])
        
        # Eng faol foydalanuvchilar
        user_activity = {}
        for log in self.user_stats:
            user_id = log['user_id']
            if user_id not in user_activity:
                user_activity[user_id] = {
                    'name': log['first_name'],
                    'username': log['username'],
                    'tests': 0
                }
            if log['activity'] == 'test_started':
                user_activity[user_id]['tests'] += 1
        
        top_users = sorted(user_activity.items(), key=lambda x: x[1]['tests'], reverse=True)[:5]
        
        stats_text = f"""📊 Bot Statistikasi

👥 Jami foydalanuvchilar: {unique_users}
📝 Boshlangan testlar: {total_tests}
✅ Tugallangan testlar: {completed_tests}
📈 Tugallash foizi: {(completed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%

🏆 Eng faol foydalanuvchilar:
"""
        
        for i, (user_id, data) in enumerate(top_users, 1):
            username = f"@{data['username']}" if data['username'] else "Noma'lum"
            stats_text += f"{i}. {data['name']} ({username}) - {data['tests']} ta test\n"
        
        return stats_text
    
    def load_data(self):
        """Savollar va tarjimalarni yuklash"""
        try:
            # Hozirgi fayl joylashgan papkani topish
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Tarjimalarni yuklash
            translations_path = os.path.join(current_dir, 'translations.json')
            with open(translations_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)

            # Ensure DB has questions for each subject; load from JSON if DB is empty
            subjects = [
                ('aviation', 'questions_aviation.json'),
                ('aviation_general', 'questions_aviation_general.json'),
                ('meteorology', 'questions_meteorology.json'),
                ('navigation', 'questions_navigation.json')
            ]
            for subj, path in subjects:
                try:
                    count = db.count_questions(subj)
                except Exception:
                    count = 0
                full_path = os.path.join(current_dir, path)
                if count == 0 and os.path.exists(full_path):
                    inserted = db.load_questions_from_json(full_path, subj)
                    logger.info(f"Inserted {inserted} questions for {subj} from {full_path}")

            logger.info("Ma'lumotlar muvaffaqiyatli yuklandi into DB")
        except FileNotFoundError as e:
            logger.error(f"Fayl topilmadi: {e}")
            self.translations = {}
    
    def get_text(self, user_id: int, key: str) -> str:
        """Foydalanuvchi tili bo'yicha matnni olish"""
        session = self.user_sessions.get(user_id, {})
        language = session.get('language', 'uz')
        return self.translations.get(language, {}).get(key, key)
    
    def start_new_quiz(self, user_id: int, subject: str):
        """Yangi quiz boshlash"""
        # Use DB to fetch random questions
        try:
            available = db.count_questions(subject)
        except Exception:
            available = 0
        if available < 30:
            logger.warning(f"{subject} uchun kamida 30 ta savol kerak!")
            return False

        selected_questions = db.get_random_questions(subject, 30)
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
            
        self.user_sessions[user_id].update({
            'subject': subject,
            'questions': selected_questions,
            'current_question': 0,
            'correct_answers': 0,
            'answers': [None] * 30,
            'state': 'quiz'
        })
        return True
    
    def get_current_question(self, user_id: int):
        """Joriy savolni olish"""
        if user_id not in self.user_sessions:
            return None
        
        session = self.user_sessions[user_id]
        current_index = session['current_question']
        
        if current_index >= len(session['questions']):
            return None
        
        return session['questions'][current_index]
    
    def answer_question(self, user_id: int, answer: str):
        """Savolga javob berish"""
        if user_id not in self.user_sessions:
            return False
        
        session = self.user_sessions[user_id]
        current_index = session['current_question']
        
        if current_index >= len(session['questions']):
            return False
        
        question = session['questions'][current_index]
        # correct_answer ni tekshirish - agar harf bo'lsa, raqamga aylantirish
        if isinstance(question['correct_answer'], str):
            # Agar "A", "B", "C", "D" shaklida bo'lsa
            if question['correct_answer'] in ['A', 'B', 'C', 'D']:
                correct_answer = ord(question['correct_answer']) - ord('A')  # A=0, B=1, C=2, D=3
            else:
                try:
                    correct_answer = int(question['correct_answer'])
                except ValueError:
                    correct_answer = 0  # Default qiymat
        else:
            correct_answer = question['correct_answer']
        
        user_answer = int(answer) if isinstance(answer, str) else answer
        is_correct = user_answer == correct_answer
        
        # Javobni saqlash
        session['answers'][current_index] = {
            'user_answer': answer,
            'is_correct': is_correct
        }
        
        if is_correct:
            session['correct_answers'] += 1
        
        return is_correct
    
    def next_question(self, user_id: int):
        """Keyingi savolga o'tish"""
        if user_id not in self.user_sessions:
            return False
        
        session = self.user_sessions[user_id]
        session['current_question'] += 1
        return True
    
    def previous_question(self, user_id: int):
        """Oldingi savolga qaytish"""
        if user_id not in self.user_sessions:
            return False
        
        session = self.user_sessions[user_id]
        if session['current_question'] > 0:
            session['current_question'] -= 1
            # Oldingi javobni o'chirish
            current_index = session['current_question']
            if session['answers'][current_index] and session['answers'][current_index]['is_correct']:
                session['correct_answers'] -= 1
            session['answers'][current_index] = None
            return True
        return False
    
    def get_progress(self, user_id: int):
        """Progress ma'lumotlarini olish"""
        if user_id not in self.user_sessions:
            return None
        
        session = self.user_sessions[user_id]
        return {
            'current': session['current_question'] + 1,
            'total': len(session['questions']),
            'correct': session['correct_answers']
        }
    
    def is_quiz_finished(self, user_id: int):
        """Quiz tugaganmi tekshirish"""
        if user_id not in self.user_sessions:
            return True
        
        session = self.user_sessions[user_id]
        return session['current_question'] >= len(session['questions'])
    
    def set_language(self, user_id: int, language: str):
        """Foydalanuvchi tilini o'rnatish"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        self.user_sessions[user_id]['language'] = language
        self.user_sessions[user_id]['state'] = 'menu'

# Global bot instance
quiz_bot = MultiLanguageQuizBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot boshlanishi - til tanlash"""
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Foydalanuvchi faoliyatini loglash (DB)
    db.log_activity(
        user_id,
        user.username,
        user.first_name,
        'bot_started',
        None,
        datetime.now().isoformat()
    )
    
    # Til tanlash tugmalari
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = "🌍 Tilni tanlang / Выберите язык / Choose language:"
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Asosiy menyu ko'rsatish"""
    start_message = quiz_bot.get_text(user_id, 'start_message')
    choose_subject = quiz_bot.get_text(user_id, 'choose_subject')
    
    menu_text = f"{start_message}\n\n{choose_subject}"
    
    # Mavzular tugmalari
    keyboard = [
        [InlineKeyboardButton(quiz_bot.get_text(user_id, 'aviation'), callback_data="subject_aviation")],
        [InlineKeyboardButton(quiz_bot.get_text(user_id, 'aviation_general'), callback_data="subject_aviation_general")],
        [InlineKeyboardButton(quiz_bot.get_text(user_id, 'meteorology'), callback_data="subject_meteorology")],
        [InlineKeyboardButton(quiz_bot.get_text(user_id, 'navigation'), callback_data="subject_navigation")],
        [InlineKeyboardButton(quiz_bot.get_text(user_id, 'choose_language'), callback_data="change_language")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(menu_text, reply_markup=reply_markup)

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Savolni ko'rsatish"""
    question = quiz_bot.get_current_question(user_id)
    progress = quiz_bot.get_progress(user_id)
    
    if not question or not progress:
        await update.callback_query.edit_message_text("❌ Xatolik yuz berdi!")
        return
    
    # Savol matni
    question_text = f"📝 **{quiz_bot.get_text(user_id, 'question')} {question['id']} ({progress['current']}/{progress['total']})**\n\n"
    question_text += f"❓ {question['question']}\n\n"
    
    # Javob variantlari
    options = ['A', 'B', 'C', 'D']
    for i, option in enumerate(options):
        if i < len(question['options']):
            question_text += f"{option}) {question['options'][i]}\n"
    
    question_text += f"\n✅ {quiz_bot.get_text(user_id, 'correct_answers')}: {progress['correct']}"
    
    # Tugmalar
    keyboard = []
    
    # Javob tugmalari (callback_data now uses option index)
    answer_buttons = []
    for i, option in enumerate(options):
        if i < len(question['options']):
            answer_buttons.append(
                InlineKeyboardButton(option, callback_data=f"answer_{i}")
            )
    
    # Javob tugmalarini 2 ta qatorga bo'lish
    keyboard.extend([answer_buttons[i:i+2] for i in range(0, len(answer_buttons), 2)])
    
    # Navigatsiya tugmalari
    nav_buttons = []
    if progress['current'] > 1:
        nav_buttons.append(InlineKeyboardButton(quiz_bot.get_text(user_id, 'back'), callback_data="prev"))
    
    nav_buttons.append(InlineKeyboardButton(quiz_bot.get_text(user_id, 'forward'), callback_data="next"))
    nav_buttons.append(InlineKeyboardButton(quiz_bot.get_text(user_id, 'restart'), callback_data="restart"))
    
    keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton(quiz_bot.get_text(user_id, 'back_to_menu'), callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            question_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            question_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugma bosilganida ishlovchi"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Til tanlash
    if data.startswith("lang_"):
        language = data.split("_")[1]
        quiz_bot.set_language(user_id, language)
        await show_main_menu(update, context, user_id)
        return
    
    # Til o'zgartirish
    if data == "change_language":
        keyboard = [
            [
                InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🌍 Tilni tanlang / Выберите язык / Choose language:", reply_markup=reply_markup)
        return
    
    # Asosiy menyu
    if data == "main_menu":
        await show_main_menu(update, context, user_id)
        return
    
    # Fan tanlash
    if data.startswith("subject_"):
        subject = data.split("_", 1)[1]  # "_"dan keyin barcha qismni olish
        if subject == "aviation" or subject == "aviation_general" or subject == "meteorology" or subject == "navigation":
            if quiz_bot.start_new_quiz(user_id, subject):
                # Test boshlanganligi haqida loglash (DB)
                user = query.from_user
                db.log_activity(
                    user_id,
                    user.username,
                    user.first_name,
                    'test_started',
                    subject,
                    datetime.now().isoformat()
                )
                
                await query.edit_message_text(quiz_bot.get_text(user_id, 'test_starting'))
                
                # 1 soniya kutib, birinchi savolni ko'rsatish
                import asyncio
                await asyncio.sleep(1)
                await show_first_question(query, context, user_id)
            else:
                await query.edit_message_text("❌ Savollar yuklanmadi!")
        return
    
    # Javob berildi
    if data.startswith("answer_"):
        # callback contains the option index, e.g. answer_0
        try:
            selected_index = int(data.split("_")[1])
        except Exception:
            selected_index = None

        is_correct = quiz_bot.answer_question(user_id, selected_index)

        if is_correct:
            await query.edit_message_text(quiz_bot.get_text(user_id, 'correct_answer'))
        else:
            q = quiz_bot.get_current_question(user_id)
            # Correct answer indeksini topish
            if isinstance(q['correct_answer'], str):
                if q['correct_answer'] in ['A', 'B', 'C', 'D']:
                    correct_idx = ord(q['correct_answer']) - ord('A')  # A=0, B=1, C=2, D=3
                else:
                    try:
                        correct_idx = int(q['correct_answer'])
                    except ValueError:
                        correct_idx = 0
            else:
                correct_idx = q['correct_answer']
            
            correct_text = q['options'][correct_idx] if 0 <= correct_idx < len(q['options']) else str(correct_idx)
            wrong_text = quiz_bot.get_text(user_id, 'wrong_answer')
            await query.edit_message_text(f"{wrong_text} {correct_text}")
        
        # 2 soniya kutish va keyingi savolga o'tish
        import asyncio
        await asyncio.sleep(2)
        await show_next_question(query, context, user_id)
        return
    
    # Navigation tugmalari
    if data == "next":
        if not quiz_bot.is_quiz_finished(user_id):
            quiz_bot.next_question(user_id)
            if quiz_bot.is_quiz_finished(user_id):
                await show_results(query, context, user_id)
            else:
                await show_question(update, context, user_id)
        else:
            await show_results(query, context, user_id)
        return
    
    if data == "prev":
        if quiz_bot.previous_question(user_id):
            await show_question(update, context, user_id)
        return
    
    if data == "restart":
        session = quiz_bot.user_sessions.get(user_id, {})
        subject = session.get('subject', 'aviation')
        quiz_bot.start_new_quiz(user_id, subject)
        await show_question(update, context, user_id)
        return

async def show_first_question(query, context, user_id):
    """Birinchi savolni ko'rsatish"""
    class FakeUpdate:
        def __init__(self, callback_query):
            self.callback_query = callback_query
            self.effective_user = callback_query.from_user
    
    fake_update = FakeUpdate(query)
    await show_question(fake_update, context, user_id)

async def show_next_question(query, context, user_id):
    """Keyingi savolni ko'rsatish"""
    quiz_bot.next_question(user_id)
    
    if quiz_bot.is_quiz_finished(user_id):
        await show_results(query, context, user_id)
    else:
        class FakeUpdate:
            def __init__(self, callback_query):
                self.callback_query = callback_query
                self.effective_user = callback_query.from_user
        
        fake_update = FakeUpdate(query)
        await show_question(fake_update, context, user_id)

async def show_results(query, context, user_id):
    """Yakuniy natijalarni ko'rsatish"""
    progress = quiz_bot.get_progress(user_id)
    if not progress:
        return
    
    # Test tugaganligi haqida loglash
    user = query.from_user
    session = quiz_bot.user_sessions.get(user_id, {})
    subject = session.get('subject', 'unknown')
    
    db.log_activity(
        user_id,
        user.username,
        user.first_name,
        'test_completed',
        subject,
        datetime.now().isoformat()
    )
    
    percentage = (progress['correct'] / progress['total']) * 100
    
    result_text = f"🎯 **{quiz_bot.get_text(user_id, 'test_completed')}**\n\n"
    result_text += f"✅ {quiz_bot.get_text(user_id, 'correct_answers')}: {progress['correct']}/{progress['total']}\n"
    result_text += f"📊 {quiz_bot.get_text(user_id, 'final_result')}: {percentage:.1f}%\n\n"
    
    if percentage >= 90:
        result_text += quiz_bot.get_text(user_id, 'excellent')
    elif percentage >= 80:
        result_text += quiz_bot.get_text(user_id, 'good')
    elif percentage >= 70:
        result_text += quiz_bot.get_text(user_id, 'satisfactory')
    else:
        result_text += quiz_bot.get_text(user_id, 'poor')
    
    keyboard = [[
        InlineKeyboardButton(quiz_bot.get_text(user_id, 'restart'), callback_data="restart"),
        InlineKeyboardButton(quiz_bot.get_text(user_id, 'back_to_menu'), callback_data="main_menu")
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """O'zingizning user ID'ingizni bilish uchun"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    user_text = f"👤 Sizning ma'lumotlaringiz:\n\n"
    user_text += f"🆔 User ID: {user_id}\n"
    user_text += f"👤 Ism: {first_name}\n"
    if username:
        user_text += f"📝 Username: @{username}"
    else:
        user_text += f"📝 Username: Yo'q"
    
    await update.message.reply_text(user_text)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin uchun statistika ko'rsatish (faqat sizning user ID'ingiz uchun)"""
    user_id = update.effective_user.id
    
    # Bu yerda o'zingizning user ID'ingizni kiriting
    ADMIN_USER_ID = 8290940402  # Sardor_w ning user ID'si
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Sizda bu komandani ishlatish huquqi yo'q!")
        return
    
    s = db.get_stats_summary()
    if not s:
        await update.message.reply_text("📊 Hozircha statistik ma'lumot yo'q")
        return

    unique_users = s.get('unique_users', 0)
    total_tests = s.get('total_tests', 0)
    completed_tests = s.get('completed_tests', 0)
    top = s.get('top_users', [])

    stats_text = f"📊 Bot Statistikasi\n\n👥 Jami foydalanuvchilar: {unique_users}\n📝 Boshlangan testlar: {total_tests}\n✅ Tugallangan testlar: {completed_tests}\n\n🏆 Eng faol foydalanuvchilar:\n"
    for i, row in enumerate(top, 1):
        uid, name, username, tests = row
        uname = f"@{username}" if username else "Noma'lum"
        stats_text += f"{i}. {name} ({uname}) - {tests} ta test\n"

    await update.message.reply_text(stats_text)

def main():
    """Botni ishga tushirish"""
    # Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", get_my_id))  # User ID olish
    application.add_handler(CommandHandler("stats", admin_stats))  # Admin statistika
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Health check uchun web server (agar kerak bo'lsa)
    port = int(os.getenv("PORT", 8080))
    
    # Botni ishga tushirish
    print("🤖 Bot ishga tushmoqda...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()