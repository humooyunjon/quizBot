import telebot
import google.generativeai as genai
import os
import json
import time
import logging
import re

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Professional Quiz Generator. Menga istalgan matnni yuboring, men undan mukammal testlar tuzib beraman.")

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_ai_quiz(message):
    sent_msg = bot.reply_to(message, "Matn tahlil qilinmoqda va savollar tuzilmoqda...")
    
    text_len = len(message.text)
    q_count = 5 if text_len < 500 else 10 if text_len < 1500 else 15

    prompt = f"""
    Berilgan matn asosida {q_count} ta test savolini tuz. 
    Javobing FAQAT va FAQAT JSON formatida bo'lishi shart. Hech qanday qo'shimcha so'z, izoh yoki markdown yozma.
    Format:
    [
      {{"question": "savol", "options": ["A", "B", "C", "D"], "correct": 0}}
    ]
    Matn: {message.text}
    """

    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if not match:
            raise ValueError("Javobdan JSON formati topilmadi")
            
        json_str = match.group(0)
        quiz_data = json.loads(json_str)
        
        bot.delete_message(message.chat.id, sent_msg.message_id)
        bot.send_message(message.chat.id, f"Tayyor. {len(quiz_data)} ta savoldan iborat test boshlanadi.")

        for item in quiz_data:
            bot.send_poll(
                chat_id=message.chat.id,
                question=item['question'][:255],
                options=[str(opt)[:100] for opt in item['options'][:4]],
                type='quiz',
                correct_option_id=int(item['correct']),
                is_anonymous=False
            )
            time.sleep(1.2)

    except Exception as e:
        logger.error(f"Xatolik: {e}")
        bot.edit_message_text(f"Xatolik yuz berdi. Iltimos, boshqa matn yuborib ko'ring. Xato: {str(e)}", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    bot.infinity_polling()