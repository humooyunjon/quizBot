import telebot
import google.generativeai as genai
import os
import json
import time
import logging

# Loglarni sozlash (Railway loglarida xatolarni ko'rish uchun)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway Variables'dan ma'lumotlarni olish
TOKEN = os.environ.get('TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini AI sozlash
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

bot = telebot.TeleBot(TOKEN)

# AI uchun ko'rsatma (Prompt)
PROMPT_TEMPLATE = """
Berilgan matn asosida 5 ta ko'p variantli test savollarini tuzing. 
Javobni FAQAT quyidagi JSON formatida qaytaring, ortiqcha tushuntirish yozmang:
[
  {{
    "question": "Savol matni",
    "options": ["A variant", "B variant", "C variant", "D variant"],
    "correct": 0
  }}
]
Matn: {text}
"""

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Salom! Men AI Quiz Generatorman. 🤖\n\nMenga biron bir mavzuda matn yuboring (kamida 50 ta belgi), men undan sizga 5 ta test tuzib beraman.")

@bot.message_handler(func=lambda message: len(message.text) > 50 and not message.text.startswith('/'))
def handle_text_to_quiz(message):
    sent_msg = bot.reply_to(message, "🤖 Matn tahlil qilinmoqda, ozgina kutib turing...")
    
    try:
        # AI ga so'rov yuborish
        response = model.generate_content(PROMPT_TEMPLATE.format(text=message.text))
        raw_text = response.text
        
        # AI javobidan faqat JSON qismini ajratib olish (xatolikni oldini olish uchun)
        try:
            start_index = raw_text.find('[')
            end_index = raw_text.rfind(']') + 1
            if start_index == -1 or end_index == 0:
                raise ValueError("JSON topilmadi")
            
            json_str = raw_text[start_index:end_index]
            quiz_data = json.loads(json_str)
        except Exception:
            # Agar find/rfind ishlamasa, oddiy almashtirishni sinab ko'radi
            json_str = raw_text.replace('```json', '').replace('```', '').strip()
            quiz_data = json.loads(json_str)
        
        # Jarayon muvaffaqiyatli bo'lsa, yuklanish xabarini o'chirish
        bot.delete_message(message.chat.id, sent_msg.message_id)
        bot.send_message(message.chat.id, f"✅ AI {len(quiz_data)} ta savol tuzdi! Marhamat:")

        # Testlarni ketma-ket yuborish
        for item in quiz_data:
            bot.send_poll(
                chat_id=message.chat.id,
                question=item['question'],
                options=item['options'],
                type='quiz',
                correct_option_id=item['correct'],
                is_anonymous=False
            )
            time.sleep(1.5) # Telegram spam deb hisoblamasligi uchun

    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {e}")
        bot.edit_message_text("❌ AI javob berishda xato qildi yoki matn juda murakkab. Iltimos, boshqa matn yuborib ko'ring.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    logger.info("AI Bot ishga tushdi...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)