import telebot
from telebot import types
import random
import time
import threading
import os
import logging

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token Railway Variables'dan olinadi
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# So'zlar bazasi
vocab = {
    "Culture": "Madaniyat", "Cultural diversity": "Madaniy xilma-xillik",
    "Multiculturalism": "Ko‘p madaniyatlilik", "Heritage": "Madaniy meros",
    "Tradition": "An’ana", "Custom": "Urf-odat", "Identity": "O‘zlik, identitet",
    "Ethnicity": "Etnik kelib chiqish", "Community": "Jamiyat, jamoa",
    "Social norms": "Ijtimoiy me’yorlar", "Values": "Qadriyatlar",
    "Beliefs": "E’tiqodlar", "Tolerance": "Bag‘rikenglik",
    "Inclusion": "Inklyuziya", "Integration": "Integratsiya",
    "Discrimination": "Kamsitish", "Inequality": "Tengsizlik",
    "Social cohesion": "Ijtimoiy birdamlik", "Globalization": "Globallashuv",
    "Migration": "Migratsiya", "Immigrant": "Muhojir", "Minority": "Ozchilik",
    "Majority": "Ko‘pchilik", "Cultural exchange": "Madaniy almashinuv",
    "Assimilation": "Moslashib singib ketish", "Intercultural": "Madaniyatlararo",
    "Diverse": "Xilma-xil", "Inclusive": "Qamrab oluvchi",
    "Tolerant": "Bag‘rikeng ", "Open-minded": "Ochiq fikrli",
    "Traditional": "An’anaviy", "Modern": "Zamonaviy", "Cultural ": "Madaniy",
    "Respectful": "Hurmatli", "Ethnically diverse": "Etnik jihatdan xilma-xil",
    "Preserve": "Saqlamoq", "Respect differences": "Farqlarga hurmat qilmoq",
    "Promote equality": "Tenglikni targ‘ib qilmoq", "Embrace diversity": "Xilma-xillikni qabul qilmoq",
    "Interact": "Muloqot qilmoq", "Coexist": "Yonma-yon yashamoq",
    "Cultural awareness": "Madaniy xabardorlik", "Social identity": "Ijtimoiy identitet",
    "Shared values": "Umumiy qadriyatlar", "Social harmony": "Ijtimoiy totuvlik",
    "Cultural conflict": "Madaniy ziddiyat", "Mutual respect": "O‘zaro hurmat",
    "Cultural understanding": "Madaniy tushunish", "Social inclusion": "Ijtimoiy inklyuziya",
    "Cultural heritage site": "Madaniy meros obyekti"
}

user_scores = {}
poll_data = {} 
game_running = False

@bot.message_handler(commands=['start_test'])
def start_game(message):
    global game_running, user_scores, poll_data
    
    if game_running:
        bot.send_message(message.chat.id, "⚠️ Test allaqachon ketmoqda!")
        return

    game_running = True
    user_scores = {} 
    poll_data = {}
    
    bot.send_message(message.chat.id, "📢 <b>TEST BOSHLANDI!</b>\n\nTayyorlaning...", parse_mode="HTML")
    time.sleep(2)
    
    # Har bir chat uchun alohida chat_type uzatiladi
    threading.Thread(target=run_quiz_loop, args=(message.chat.id, message.chat.type)).start()

@bot.message_handler(commands=['stopit'])
def stop_game(message):
    global game_running
    if game_running:
        game_running = False
        bot.send_message(message.chat.id, "🛑 Test to'xtatildi.")
        finish_game(message.chat.id, message.chat.type)
    else:
        bot.send_message(message.chat.id, "Hozir hech qanday test ketmayapti.")

def run_quiz_loop(chat_id, chat_type):
    global game_running, poll_data
    items = list(vocab.items())
    random.shuffle(items)
    
    for index, (english, uzbek) in enumerate(items, 1):
        if not game_running: return
        
        all_translations = list(vocab.values())
        wrong_options = random.sample([t for t in all_translations if t != uzbek], 3)
        options = wrong_options + [uzbek]
        random.shuffle(options)
        correct_id = options.index(uzbek)
        
        try:
            poll_msg = bot.send_poll(
                chat_id=chat_id,
                question=f"№{index}/50: {english}?",
                options=options,
                type='quiz',
                correct_option_id=correct_id,
                is_anonymous=False,
                open_period=10
            )
            # chat_type ma'lumotini poll_id bilan bog'lab saqlaymiz
            poll_data[poll_msg.poll.id] = {"correct": correct_id, "chat_type": chat_type}
            
            for _ in range(10):
                if not game_running: return
                time.sleep(1)
        except Exception as e:
            logger.error(f"Xatolik: {e}")
            continue

    if game_running:
        game_running = False
        finish_game(chat_id, chat_type)

@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    global user_scores, poll_data
    poll_id = poll_answer.poll_id
    if poll_id not in poll_data: return
    
    user_id = poll_answer.user.id
    user_name = poll_answer.user.first_name
    selected_option = poll_answer.option_ids[0]
    
    current_time = time.time()
    if user_id not in user_scores:
        user_scores[user_id] = {
            "name": user_name, 
            "score": 0, 
            "start_time": current_time, 
            "last_time": current_time
        }
    
    if selected_option == poll_data[poll_id]["correct"]:
        user_scores[user_id]["score"] += 1
        user_scores[user_id]["last_time"] = current_time

def finish_game(chat_id, chat_type):
    if not user_scores:
        bot.send_message(chat_id, "🏆 <b>Natijalar:</b>\nHech kim qatnashmadi.", parse_mode="HTML")
        return

    if chat_type == 'private':
        # Shaxsiy xabarda shunchaki umumiy ball
        for player in user_scores.values():
            bot.send_message(chat_id, f"✅ Test tugadi!\nSizning natijangiz: {player['score']} ta to'g'ri javob.")
    else:
        # Guruhda to'liq leaderboard
        leaderboard = "🏆 <b>GURUH NATIJALARI</b> 🏆\n\n"
        sorted_scores = sorted(
            user_scores.values(), 
            key=lambda x: (-x['score'], x['last_time'] - x['start_time'])
        )
        for i, player in enumerate(sorted_scores, 1):
            duration = int(player['last_time'] - player['start_time'])
            minutes = duration // 60
            seconds = duration % 60
            time_display = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
            leaderboard += f"{i}. {player['name']} — {player['score']} ball ({time_display})\n"
        bot.send_message(chat_id, leaderboard, parse_mode="HTML")

if __name__ == "__main__":
    logger.info("Bot ishga tushdi...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)