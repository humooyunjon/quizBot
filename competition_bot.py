import telebot
import google.generativeai as genai
import os
import json
import time
import logging
import re

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway Variables (TOKEN va GEMINI_API_KEY Railway'da bo'lishi shart)
TOKEN = os.environ.get('TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini AI konfiguratsiyasi (2026-yilgi eng so'nggi model)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-3.1-flash')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = (
        "🚀 **Professional AI Quiz Generator v3.1**\n\n"
        "Menga istalgan tilda matn yuboring, men undan darhol "
        "mukammal testlar tuzib beraman.\n\n"
        "Matn uzunligiga qarab savollar soni avtomatik belgilanadi."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_ai_quiz(message):
    sent_msg = bot.reply_to(message, "🧠 Gemini 3.1 Flash matnni tahlil qilmoqda...")
    
    # Matn uzunligiga qarab savollar sonini belgilash
    text_len = len(message.text)
    q_count = 5 if text_len < 500 else 10 if text_len < 1500 else 15

    prompt = f"""
    Berilgan matn asosida {q_count} ta mantiqiy test savollarini tuz. 
    Javobni FAQAT JSON formatida qaytar, hech qanday ortiqcha so'z yozma.
    Format:
    [
      {{"question": "savol", "options": ["A", "B", "C", "D"], "correct": 0}}
    ]
    Matn: {message.text}
    """

    try:
        # AI dan javob olish
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # JSONni Regex orqali sug'urib olish (barqarorlik uchun)
        match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if not match:
            raise ValueError("AI JSON formatida javob bermadi.")
            
        quiz_data = json.loads(match.group(0))
        
        bot.delete_message(message.chat.id, sent_msg.message_id)
        bot.send_message(message.chat.id, f"✅ Tayyor! {len(quiz_data)} ta savoldan iborat test boshlanadi.")

        for item in quiz_data:
            # Telegram limitlariga moslash
            question = item['question'][:255]
            options = [str(opt)[:100] for opt in item['options'][:4]]
            
            bot.send_poll(
                chat_id=message.chat.id,
                question=question,
                options=options,
                type='quiz',
                correct_option_id=int(item['correct']),
                is_anonymous=False
            )
            time.sleep(1.2) # Flood protection

    except Exception as e:
        logger.error(f"Xatolik: {str(e)}")
        bot.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    logger.info("Bot v3.1 ishga tushdi...")
    bot.infinity_polling()