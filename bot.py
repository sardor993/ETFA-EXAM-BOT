import logging
import json
import random
import os
from typing import Dict, Any
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

class QuizBot:
    def __init__(self):
        self.questions = self.load_questions()
        self.user_sessions = {}  # Har bir user uchun sessiya ma'lumotlari
    
    def load_questions(self):
        """Savollarni JSON fayldan yuklash"""
        try:
            with open('questions.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("questions.json fayli topilmadi!")
            return []
    
    def start_new_quiz(self, user_id: int):
        """Yangi quiz boshlash - 30 ta random savol tanlash"""
        if len(self.questions) < 30:
            logger.warning("Kamida 30 ta savol kerak!")
            return False
        
        selected_questions = random.sample(self.questions, 30)
        
        self.user_sessions[user_id] = {
            'questions': selected_questions,
            'current_question': 0,
            'correct_answers': 0,
            'answers': [None] * 30  # Foydalanuvchi javoblari
        }
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
        is_correct = answer == question['correct_answer']
        
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
            # Oldingi javobni o'chirish (qayta javob berish uchun)
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

# Global bot instance
quiz_bot = QuizBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot boshlanishi"""
    user_id = update.effective_user.id
    
    if not quiz_bot.start_new_quiz(user_id):
        await update.message.reply_text(
            "❌ Xatolik yuz berdi. Savollar yuklanmadi yoki kamida 30 ta savol kerak!"
        )
        return
    
    await show_question(update, context, user_id)

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Savolni ko'rsatish"""
    question = quiz_bot.get_current_question(user_id)
    progress = quiz_bot.get_progress(user_id)
    
    if not question or not progress:
        await update.message.reply_text("❌ Xatolik yuz berdi!")
        return
    
    # Savol matni
    question_text = f"📝 **Savol {progress['current']}/{progress['total']}**\n\n"
    question_text += f"❓ {question['question']}\n\n"
    
    # Javob variantlari
    options = ['A', 'B', 'C', 'D']
    for i, option in enumerate(options):
        if i < len(question['options']):
            question_text += f"{option}) {question['options'][i]}\n"
    
    question_text += f"\n✅ To'g'ri javoblar: {progress['correct']}"
    
    # Tugmalar
    keyboard = []
    
    # Javob tugmalari
    answer_buttons = []
    for i, option in enumerate(options):
        if i < len(question['options']):
            answer_buttons.append(
                InlineKeyboardButton(option, callback_data=f"answer_{option}")
            )
    
    # Javob tugmalarini 2 ta qatorga bo'lish
    keyboard.extend([answer_buttons[i:i+2] for i in range(0, len(answer_buttons), 2)])
    
    # Navigatsiya tugmalari
    nav_buttons = []
    if progress['current'] > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Orqaga", callback_data="prev"))
    
    nav_buttons.append(InlineKeyboardButton("➡️ Oldinga", callback_data="next"))
    nav_buttons.append(InlineKeyboardButton("🔄 Qayta boshlash", callback_data="restart"))
    
    keyboard.append(nav_buttons)
    
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
    
    if data.startswith("answer_"):
        # Javob berildi
        answer = data.split("_")[1]
        is_correct = quiz_bot.answer_question(user_id, answer)
        
        # Javob to'g'ri yoki noto'g'ri ekanligini ko'rsatish
        if is_correct:
            await query.edit_message_text("✅ To'g'ri javob!")
        else:
            correct_answer = quiz_bot.get_current_question(user_id)['correct_answer']
            await query.edit_message_text(f"❌ Noto'g'ri! To'g'ri javob: {correct_answer}")
        
        # 2 soniya kutish
        context.application.job_queue.run_once(
            lambda context: show_next_question(query, context, user_id),
            2
        )
    
    elif data == "next":
        # Keyingi savol
        if not quiz_bot.is_quiz_finished(user_id):
            quiz_bot.next_question(user_id)
            if quiz_bot.is_quiz_finished(user_id):
                await show_results(query, context, user_id)
            else:
                await show_question(update, context, user_id)
        else:
            await show_results(query, context, user_id)
    
    elif data == "prev":
        # Oldingi savol
        if quiz_bot.previous_question(user_id):
            await show_question(update, context, user_id)
    
    elif data == "restart":
        # Qayta boshlash
        quiz_bot.start_new_quiz(user_id)
        await show_question(update, context, user_id)

async def show_next_question(query, context, user_id):
    """Keyingi savolni ko'rsatish (javobdan keyin)"""
    quiz_bot.next_question(user_id)
    
    if quiz_bot.is_quiz_finished(user_id):
        await show_results(query, context, user_id)
    else:
        # Update obyektini yaratish
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
    
    percentage = (progress['correct'] / progress['total']) * 100
    
    result_text = f"🎯 **Test yakunlandi!**\n\n"
    result_text += f"✅ To'g'ri javoblar: {progress['correct']}/{progress['total']}\n"
    result_text += f"📊 Natija: {percentage:.1f}%\n\n"
    
    if percentage >= 90:
        result_text += "🏆 A'lo! Siz juda yaxshi natija ko'rsatdingiz!"
    elif percentage >= 80:
        result_text += "👍 Yaxshi! Deyarli mukammal natija!"
    elif percentage >= 70:
        result_text += "😊 Qoniqarli! Biroz mashq qiling va yaxshiroq bo'ladi!"
    else:
        result_text += "😔 Mavzuni qayta o'rganing va boshidan urinib ko'ring!"
    
    keyboard = [[
        InlineKeyboardButton("🔄 Qayta boshlash", callback_data="restart"),
        InlineKeyboardButton("📊 Batafsil natija", callback_data="detailed_results")
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def main():
    """Botni ishga tushirish"""
    # Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Botni ishga tushirish
    print("🤖 Bot ishga tushmoqda...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()