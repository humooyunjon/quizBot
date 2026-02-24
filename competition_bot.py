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
model = genai.GenerativeModel('gemini-2.5-pro')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Professional Quiz Generator ishga tushdi. Menga matn yuboring.")

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_ai_quiz(message):
    sent_msg = bot.reply_to(message, "Matn tahlil qilinmoqda...")
    
    text_len = len(message.text)
    q_count = 5 if text_len < 500 else 10 if text_len < 1500 else 15

    prompt = f'''
    Berilgan matn asosida {q_count} ta test savolini tuz. 
    Javobing FAQAT JSON formatida bo'lishi shart. Boshqa so'z yozma.
    Format:
    [
      {{"question": "savol", "options": ["A", "B", "C", "D"], "correct": 0}}
    ]
    Matn: {message.text}
    '''

    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        
        if not match:
            raise ValueError("JSON topilmadi")
            
        quiz_data = json.loads(match.group(0))
        
        bot.delete_message(message.chat.id, sent_msg.message_id)
        bot.send_message(message.chat.id, f"Tayyor. {len(quiz_data)} ta savol yuborilmoqda.")

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
        logger.error(f"Xatolik: {str(e)}")
        bot.edit_message_text(f"Xatolik yuz berdi: {str(e)}", message.chat.id, sent_msg.message_id)

if __name__ == '__main__':
    bot.infinity_polling()