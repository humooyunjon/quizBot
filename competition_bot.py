import telebot
import google.generativeai as genai
import os
import json
import time
import logging

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway Variables
TOKEN = os.environ.get('TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini AI konfiguratsiyasi (Modelga shaxsiyat beramiz)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # Tezroq va aqlliroq model
    generation_config={"response_mime_type": "application/json"} # FAQAT JSON qaytarishni majburlash
)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🚀 **Professional AI Quiz Generator v2.0**\n\nMenga istalgan matnni yuboring, men undan mukammal testlar tuzib beraman. Endi hech qanday cheklovlar yo'q!", parse_mode="Markdown")

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_ai_quiz(message):
    sent_msg = bot.reply_to(message, "🧠 AI matnni tahlil qilmoqda va savollar tuzmoqda...")
    
    # Matn uzunligiga qarab savollar sonini belgilash
    text_len = len(message.text)
    q_count = 5 if text_len < 500 else 10 if text_len < 1500 else 15

    prompt = f"""
    Berilgan matn asosida {q_count} ta qiziqarli va mantiqiy test savollarini tuz. 
    Javobni FAQAT JSON formatida qaytar:
    [
      {{"question": "savol", "options": ["A", "B", "C", "D"], "correct": 0}}
    ]
    Matn: {message.text}
    """

    try:
        # AI dan javob olish
        response = model.generate_content(prompt)
        
        # Generation_config JSON majburlagani uchun to'g'ridan-to'g'ri o'qiymiz
        quiz_data = json.loads(response.text)
        
        bot.delete_message(message.chat.id, sent_msg.message_id)
        bot.send_message(message.chat.id, f"✅ Tayyor! {len(quiz_data)} ta savoldan iborat intellektual test boshlanadi.")

        for item in quiz_data:
            bot.send_poll(
                chat_id=message.chat.id,
                question=item['question'][:255], # Telegram limiti
                options=[opt[:100] for opt in item['options'][:4]], # Telegram limiti
                type='quiz',
                correct_option_id=int(item['correct']),
                is_anonymous=False
            )
            time.sleep(1.2)

    except Exception as e:
        logger.error(f"Xatolik: {e}")
        bot.edit_message_text("❌ Xatolik: Matn mazmunsiz yoki AI tushunmadi. Iltimos, ma'lumotga boyroq matn yuboring.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    bot.infinity_polling()