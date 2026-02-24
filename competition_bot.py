import telebot
import google.generativeai as genai
import os
import json
import random
import time

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
Javobni FAQAT quyidagi JSON formatida qaytaring:
[
  {
    "question": "Savol matni",
    "options": ["A variant", "B variant", "C variant", "D variant"],
    "correct": 0
  }
]
Matn: {text}
"""

@bot.message_handler(func=lambda message: len(message.text) > 50 and not message.text.startswith('/'))
def handle_text_to_quiz(message):
    sent_msg = bot.reply_to(message, "🤖 Matn tahlil qilinmoqda, ozgina kutib turing...")
    
    try:
        # AI ga so'rov yuborish
        response = model.generate_content(PROMPT_TEMPLATE.format(text=message.text))
        
        # JSONni tozalash va o'qish
        quiz_data = json.loads(response.text.replace('```json', '').replace('```', ''))
        
        bot.delete_message(message.chat.id, sent_msg.message_id)
        bot.send_message(message.chat.id, f"✅ AI {len(quiz_data)} ta savol tuzdi! Testni boshlaymiz.")

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
            time.sleep(1) # Telegram limitidan oshmaslik uchun

    except Exception as e:
        bot.edit_message_text("❌ Xatolik yuz berdi. Matn juda qisqa yoki AI tushunmadi.", message.chat.id, sent_msg.message_id)
        print(f"Error: {e}")

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Salom! Menga uzunroq matn yuboring, men undan avtomatik test tuzib beraman.")

bot.infinity_polling()