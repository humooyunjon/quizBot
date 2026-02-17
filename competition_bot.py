import telebot
from telebot import types
import random
import time
import threading

# 1. O'z tokeningizni qo'ying
TOKEN = '8227991509:AAED-PzSMDZqlDK_hSMGdNvlYputCpDDn4A'
bot = telebot.TeleBot(TOKEN)

# 2. So'zlar bazasi
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

# O'yin holati va ma'lumotlar
user_scores = {}
poll_data = {} 
game_running = False

@bot.message_handler(commands=['start_test'])
def start_game(message):
    global game_running, user_scores, poll_data
    
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "❌ Bu buyruq faqat guruhda ishlaydi!")
        return

    if game_running:
        bot.send_message(message.chat.id, "⚠️ O'yin allaqachon ketmoqda!")
        return

    game_running = True
    user_scores = {} 
    poll_data = {}
    
    bot.send_message(message.chat.id, "📢 <b>QUIZ BOSHLANDI!</b>\n\n50 ta savol, har biri 10 soniya.\nNatijalarda ball va sarflangan vaqt hisobga olinadi.\nTayyorlaning...", parse_mode="HTML")
    time.sleep(3)
    
    threading.Thread(target=run_quiz_loop, args=(message.chat.id,)).start()

@bot.message_handler(commands=['stop'])
def stop_game(message):
    global game_running
    if game_running:
        game_running = False # Tsiklni to'xtatish uchun signal
        bot.send_message(message.chat.id, "🛑 O'yin administrator tomonidan to'xtatildi.")
        # To'xtatilgan vaqtdagi natijalarni ko'rsatamiz
        finish_game(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Hozir hech qanday o'yin ketmayapti.")

def run_quiz_loop(chat_id):
    global game_running, poll_data
    
    items = list(vocab.items())
    random.shuffle(items)
    
    for index, (english, uzbek) in enumerate(items, 1):
        # Har bir savoldan oldin o'yin to'xtatilganini tekshiramiz
        if not game_running: 
            return
        
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
            
            poll_data[poll_msg.poll.id] = correct_id
            
            # 10 soniya kutish (o'yin to'xtatilishini tez-tez tekshirish uchun qisqa kutishlar)
            for _ in range(10):
                if not game_running: return
                time.sleep(1)
            
        except Exception as e:
            print(f"Xatolik: {e}")
            continue

    if game_running:
        game_running = False
        finish_game(chat_id)

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
    
    if selected_option == poll_data[poll_id]:
        user_scores[user_id]["score"] += 1
        user_scores[user_id]["last_time"] = current_time

def finish_game(chat_id):
    # Agar hech kim javob bermagan bo'lsa natija chiqarmaymiz
    if not user_scores:
        bot.send_message(chat_id, "🏆 <b>Natijalar:</b>\nHech kim qatnashmadi.", parse_mode="HTML")
        return

    leaderboard = "🏆 <b>MUSOBAQA NATIJALARI</b> 🏆\n\n"
    
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

print("Bot ishga tushdi...")
bot.infinity_polling()