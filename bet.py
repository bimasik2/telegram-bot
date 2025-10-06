import telebot
import requests
import json
import random
import time
import threading
import os

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8404206641:AAEwYOgnkoo1USe7Ckqtxq7e0CXy-qBdEWQ")
ADMIN_IDS = [123456789]  # ID администраторов

bot = telebot.TeleBot(BOT_TOKEN)

# Файл для сохранения данных
DATA_FILE = "user_data.json"

# Функция загрузки данных
def load_user_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print("✅ Данные игроков загружены!")
                return data
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
    return {"balances": {}, "last_used": {}}

# Функция сохранения данных
def save_user_data():
    try:
        if hasattr(farm_money, 'user_balances') and hasattr(farm_money, 'last_used'):
            data = {
                "balances": farm_money.user_balances,
                "last_used": farm_money.last_used
            }
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("💾 Данные сохранены!")
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")

# Функция автосохранения
def autosave_worker():
    while True:
        time.sleep(300)  # Сохраняем каждые 5 минут
        save_user_data()

# Обновленная система боссов с авто-спавном
boss_data = {
    "active": False,
    "hp": 0,
    "max_hp": 0,
    "name": "", 
    "reward": 0,
    "attackers": {},
    "stunned_players": {},
    "message_id": None,
    "chat_id": None,
    "last_spawn_time": 0
}

# Словари для отслеживания активности
chat_last_activity = {}
user_activity = {}
top_last_used = {}
attack_last_used = {}
casino_last_used = {}

# Загрузка данных при запуске
user_data = load_user_data()

# Функция авто-спавна босса
def auto_spawn_boss():
    while True:
        try:
            current_time = time.time()
            
            # Спавним каждые 25 минут (1500 секунд)
            if not boss_data["active"] and current_time - boss_data["last_spawn_time"] > 1500:
                # Получаем активные чаты (где была активность за последний час)
                active_chats = []
                for chat_id, last_activity in chat_last_activity.items():
                    if current_time - last_activity < 3600:  # 1 час
                        active_chats.append(chat_id)
                
                if active_chats:
                    # Выбираем случайный активный чат
                    chat_id = random.choice(active_chats)
                    
                    # Создаем улучшенного босса
                    bosses = [
                        {"name": "🔥 Огненный Дракон", "hp": 10000, "reward": 5000},
                        {"name": "❄️ Ледяной Гигант", "hp": 8000, "reward": 4000},
                        {"name": "⚡ Электро Голем", "hp": 12000, "reward": 6000},
                        {"name": "🌪️ Вихревой Демон", "hp": 9000, "reward": 4500},
                        {"name": "💀 Король Теней", "hp": 15000, "reward": 7500}
                    ]
                    
                    boss = random.choice(bosses)
                    boss_data.update({
                        "active": True,
                        "hp": boss["hp"],
                        "max_hp": boss["hp"],
                        "name": boss["name"],
                        "reward": boss["reward"],
                        "attackers": {},
                        "stunned_players": {},
                        "message_id": None,
                        "chat_id": chat_id,
                        "last_spawn_time": current_time
                    })
                    
                    # Создаем сообщение с кнопкой атаки
                    markup = telebot.types.InlineKeyboardMarkup()
                    attack_button = telebot.types.InlineKeyboardButton(
                        text="⚔️ АТАКОВАТЬ", 
                        callback_data="boss_attack"
                    )
                    markup.add(attack_button)
                    
                    boss_text = f"🎯 ПОЯВИЛСЯ БОСС!\n\n{boss['name']}\nHP: {boss['hp']}/{boss['hp']}\n\nНаграда за победу: {boss['reward']}₽\n\nНажми кнопку чтобы атаковать!"
                    sent_message = bot.send_message(chat_id, boss_text, reply_markup=markup)
                    boss_data["message_id"] = sent_message.message_id
                    
                    print(f"🦖 Босс заспавнился в чате {chat_id}")
                    
                    # Запускаем систему оглушения
                    start_stun_system()
            
            time.sleep(60)  # Проверяем каждую минуту
            
        except Exception as e:
            print(f"❌ Ошибка в авто-спавне босса: {e}")
            time.sleep(60)

# Система оглушения игроков
def start_stun_system():
    def stun_worker():
        stun_count = 0
        while boss_data["active"] and stun_count < 3:
            try:
                # Ждем случайное время между оглушениями (5-15 секунд)
                stun_delay = random.randint(5, 15)
                time.sleep(stun_delay)
                
                if boss_data["active"] and boss_data["attackers"]:
                    # Выбираем случайного атакующего для оглушения
                    attackers_list = list(boss_data["attackers"].keys())
                    if attackers_list:
                        stunned_player = random.choice(attackers_list)
                        
                        # Оглушаем на 20 секунд
                        stun_end_time = time.time() + 20
                        boss_data["stunned_players"][stunned_player] = stun_end_time
                        
                        # Уведомляем в чате
                        try:
                            user_info = bot.get_chat(stunned_player)
                            username = f"@{user_info.username}" if user_info.username else user_info.first_name
                            stun_message = f"💫 {username} оглушен боссом! Не может атаковать 20 секунд!"
                            bot.send_message(boss_data["chat_id"], stun_message)
                        except:
                            pass
                        
                        stun_count += 1
                        print(f"💫 Игрок {stunned_player} оглушен")
                
            except Exception as e:
                print(f"❌ Ошибка в системе оглушения: {e}")
                time.sleep(5)
    
    # Запускаем оглушение в отдельном потоке
    stun_thread = threading.Thread(target=stun_worker, daemon=True)
    stun_thread.start()

# Обработчик кнопки атаки
@bot.callback_query_handler(func=lambda call: call.data == "boss_attack")
def handle_boss_attack(call):
    try:
        if not boss_data["active"]:
            bot.answer_callback_query(call.id, "❌ Босс уже побежден!")
            return
        
        user_id = call.from_user.id
        current_time = time.time()
        
        # Проверяем оглушение
        if user_id in boss_data["stunned_players"]:
            stun_remaining = boss_data["stunned_players"][user_id] - current_time
            if stun_remaining > 0:
                bot.answer_callback_query(
                    call.id, 
                    f"❌ Вы оглушены! Ждите {int(stun_remaining)} секунд", 
                    show_alert=True
                )
                return
        
        # Проверка кд атаки (3 секунды)
        if user_id in attack_last_used:
            time_passed = current_time - attack_last_used[user_id]
            if time_passed < 3:
                bot.answer_callback_query(call.id, "❌ Атака перезаряжается!", show_alert=True)
                return
        
        attack_last_used[user_id] = current_time
        
        # Урон от 100 до 500
        damage = random.randint(100, 500)
        boss_data["hp"] -= damage
        
        # Записываем урон игрока
        if user_id not in boss_data["attackers"]:
            boss_data["attackers"][user_id] = {"damage": 0, "username": call.from_user.first_name}
        
        boss_data["attackers"][user_id]["damage"] += damage
        
        # Обновляем сообщение с боссом
        hp_percent = (boss_data["hp"] / boss_data["max_hp"]) * 100
        progress_bar = "█" * int(hp_percent / 10) + "░" * (10 - int(hp_percent / 10))
        
        # Создаем обновленную клавиатуру
        markup = telebot.types.InlineKeyboardMarkup()
        attack_button = telebot.types.InlineKeyboardButton(
            text="⚔️ АТАКОВАТЬ", 
            callback_data="boss_attack"
        )
        markup.add(attack_button)
        
        boss_text = f"🎯 БОСС АТАКУЕТ!\n\n{boss_data['name']}\n{progress_bar} {boss_data['hp']}/{boss_data['max_hp']} HP\n\nНаграда: {boss_data['reward']}₽\n\nНажми кнопку чтобы атаковать!"
        
        try:
            bot.edit_message_text(
                chat_id=boss_data["chat_id"],
                message_id=boss_data["message_id"],
                text=boss_text,
                reply_markup=markup
            )
        except:
            pass
        
        # Проверяем победу
        if boss_data["hp"] <= 0:
            # Награждаем всех атакующих
            winners_text = f"🎉 БОСС ПОБЕЖДЕН!\n\n{boss_data['name']} уничтожен!\n\n"
            total_reward = boss_data["reward"]
            
            for attacker_id, data in boss_data["attackers"].items():
                reward = total_reward + data["damage"] // 5
                if attacker_id not in farm_money.user_balances:
                    farm_money.user_balances[attacker_id] = 0
                farm_money.user_balances[attacker_id] += reward
                
                try:
                    user_info = bot.get_chat(attacker_id)
                    username = f"@{user_info.username}" if user_info.username else data["username"]
                except:
                    username = data["username"]
                
                winners_text += f"{username} +{reward}₽ (урон: {data['damage']})\n"
            
            bot.send_message(boss_data["chat_id"], winners_text)
            boss_data["active"] = False
            
            # Сохраняем данные после победы над боссом
            save_user_data()
        
        bot.answer_callback_query(call.id, f"✅ Нанесено {damage} урона!")
        
    except Exception as e:
        print(f"❌ Ошибка в атаке босса: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка атаки!")

# Функция напоминания
def reminder_worker():
    while True:
        try:
            current_time = time.time()
            for chat_id, last_activity in list(chat_last_activity.items()):
                # Проверяем прошло ли 10 минут (600 секунд)
                if current_time - last_activity > 600:
                    try:
                        bot.send_message(chat_id, "Что-то вы давно мною не пользовались☹️ /farma")
                        # Обновляем время чтобы не спамить
                        chat_last_activity[chat_id] = current_time
                    except:
                        # Если чат не найден или ошибка - удаляем из отслеживания
                        if chat_id in chat_last_activity:
                            del chat_last_activity[chat_id]
            time.sleep(60)  # Проверяем каждую минуту
        except Exception as e:
            print(f"❌ Ошибка в напоминаниях: {e}")
            time.sleep(60)

# Запуск потоков
reminder_thread = threading.Thread(target=reminder_worker, daemon=True)
reminder_thread.start()

boss_auto_spawn_thread = threading.Thread(target=auto_spawn_boss, daemon=True)
boss_auto_spawn_thread.start()

autosave_thread = threading.Thread(target=autosave_worker, daemon=True)
autosave_thread.start()

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        welcome_text = "Привет это бот Minerdodster203 для чата минера203, добавь меня в свой чат командой /add, /help показать команды"
        bot.reply_to(message, welcome_text)
    except Exception as e:
        print(f"❌ Ошибка в /start: {e}")

# Команда /add
@bot.message_handler(commands=['add'])
def add_to_chat(message):
    try:
        markup = telebot.types.InlineKeyboardMarkup()
        url_button = telebot.types.InlineKeyboardButton(
            text="Добавить в свой чат", 
            url="https://t.me/Dodsterchat203_bot?startgroup=true"
        )
        markup.add(url_button)
        bot.send_message(
            message.chat.id, 
            "Нажмите кнопку ниже чтобы добавить бота в ваш чат:", 
            reply_markup=markup
        )
    except Exception as e:
        print(f"❌ Ошибка в /add: {e}")

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    try:
        help_text = "список комманд:\n/farma-фармить бабосики\n/top-топ фармеров\n/casino-играть в казино\n\n⚔️ Босс появляется автоматически каждые 25 минут!"
        bot.reply_to(message, help_text)
    except Exception as e:
        print(f"❌ Ошибка в /help: {e}")

# Команда /top с кд 25 секунд (35 ИГРОКОВ)
@bot.message_handler(commands=['top'])
def show_top_users(message):
    try:
        user_id = message.from_user.id
        current_time = time.time()
        
        # Проверка кд
        if user_id in top_last_used:
            time_passed = current_time - top_last_used[user_id]
            if time_passed < 25:
                remaining_time = 25 - int(time_passed)
                bot.reply_to(message, f"❌Топ обновляется раз в 25 секунд. Подожди {remaining_time} секунд❌")
                return
        
        top_last_used[user_id] = current_time
        
        # Обновляем активность чата
        if message.chat.type in ['group', 'supergroup']:
            chat_last_activity[message.chat.id] = time.time()
        
        # Сортируем пользователей по балансу (35 ИГРОКОВ)
        if hasattr(farm_money, 'user_balances') and farm_money.user_balances:
            sorted_users = sorted(farm_money.user_balances.items(), key=lambda x: x[1], reverse=True)[:35]
            
            top_text = "🏆 Топ 35 фармеров flipper zero:\n\n"
            for i, (user_id, balance) in enumerate(sorted_users, 1):
                try:
                    user_info = bot.get_chat(user_id)
                    username = f"@{user_info.username}" if user_info.username else user_info.first_name
                    # Обрезаем длинные имена
                    if len(username) > 20:
                        username = username[:20] + "..."
                    top_text += f"{i}. {username} - {balance}₽\n"
                except:
                    top_text += f"{i}. ID:{user_id} - {balance}₽\n"
        else:
            top_text = "📊 Пока никто не фармил. Будь первым! /farma"
        
        bot.reply_to(message, top_text)
    except Exception as e:
        print(f"❌ Ошибка в /top: {e}")

# Команда /casino
@bot.message_handler(commands=['casino'])
def casino_game(message):
    try:
        # Проверка кд 30 секунд
        user_id = message.from_user.id
        current_time = time.time()
        
        if user_id in casino_last_used:
            time_passed = current_time - casino_last_used[user_id]
            if time_passed < 30:
                remaining_time = 30 - int(time_passed)
                bot.reply_to(message, f"❌ Казино перезаряжается! Жди {remaining_time} секунд")
                return
        
        casino_last_used[user_id] = current_time
        
        # Получаем баланс пользователя
        if user_id not in farm_money.user_balances:
            farm_money.user_balances[user_id] = 0
        
        balance = farm_money.user_balances[user_id]
        
        if balance < 100:
            bot.reply_to(message, "❌ Минимальная ставка - 100₽. Сначала поднакопи!")
            return
        
        # Создаем клавиатуру со ставками
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        buttons = [
            telebot.types.InlineKeyboardButton("100₽", callback_data="casino_bet:100"),
            telebot.types.InlineKeyboardButton("500₽", callback_data="casino_bet:500"),
            telebot.types.InlineKeyboardButton("1000₽", callback_data="casino_bet:1000"),
            telebot.types.InlineKeyboardButton("2000₽", callback_data="casino_bet:2000"),
            telebot.types.InlineKeyboardButton("5000₽", callback_data="casino_bet:5000"),
            telebot.types.InlineKeyboardButton("ВСЁ 💰", callback_data="casino_bet:all")
        ]
        markup.add(*buttons)
        
        casino_text = f"🎰 КАЗИНО Flipper Zero\n\nТвой баланс: {balance}₽\n\nВыбери ставку:"
        bot.send_message(message.chat.id, casino_text, reply_markup=markup)
        
    except Exception as e:
        print(f"❌ Ошибка в /casino: {e}")

# Обработчик ставок в казино
@bot.callback_query_handler(func=lambda call: call.data.startswith('casino_bet:'))
def handle_casino_bet(call):
    try:
        user_id = call.from_user.id
        bet_data = call.data.split(':')[1]
        
        # Получаем текущий баланс
        if user_id not in farm_money.user_balances:
            farm_money.user_balances[user_id] = 0
        
        balance = farm_money.user_balances[user_id]
        
        # Определяем сумму ставки
        if bet_data == "all":
            bet_amount = balance
        else:
            bet_amount = int(bet_data)
        
        # Проверяем возможность ставки
        if bet_amount < 100:
            bot.answer_callback_query(call.id, "❌ Минимальная ставка - 100₽!", show_alert=True)
            return
        
        if bet_amount > balance:
            bot.answer_callback_query(call.id, "❌ Недостаточно средств!", show_alert=True)
            return
        
        if bet_amount > 10000:
            bot.answer_callback_query(call.id, "❌ Максимальная ставка - 10,000₽!", show_alert=True)
            return
        
        # Игровой процесс
        result = random.random()
        
        if result < 0.45:
            outcome = "lose"
            multiplier = 0
            win_amount = -bet_amount
            result_text = "💔 ПРОИГРЫШ"
            emoji = "💔"
        
        elif result < 0.90:
            outcome = "win"
            multiplier = 1
            win_amount = bet_amount
            result_text = "✅ ВЫИГРЫШ x1"
            emoji = "✅"
        
        elif result < 0.98:
            outcome = "double"
            multiplier = 2
            win_amount = bet_amount * 2
            result_text = "🎉 УДВОЕНИЕ x2"
            emoji = "🎉"
        
        else:
            outcome = "jackpot"
            multiplier = 5
            win_amount = bet_amount * 5
            result_text = "🎰 ДЖЕКПОТ x5"
            emoji = "🎰"
        
        # Обновляем баланс
        farm_money.user_balances[user_id] += win_amount
        new_balance = farm_money.user_balances[user_id]
        
        # СОХРАНЯЕМ ДАННЫЕ ПОСЛЕ ИГРЫ
        save_user_data()
        
        # Формируем результат
        if win_amount > 0:
            result_message = f"{emoji} {result_text}\n\nСтавка: {bet_amount}₽\nВыигрыш: +{win_amount}₽\n\nНовый баланс: {new_balance}₽"
        else:
            result_message = f"{emoji} {result_text}\n\nСтавка: {bet_amount}₽\nПроигрыш: {win_amount}₽\n\nНовый баланс: {new_balance}₽"
        
        # Обновляем сообщение
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=result_message
        )
        
        bot.answer_callback_query(call.id, f"Результат: {result_text}")
        
    except Exception as e:
        print(f"❌ Ошибка в обработке ставки: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка в казино!", show_alert=True)

# Команда /farma
@bot.message_handler(commands=['farma'])
def farm_money(message):
    try:
        # Инициализация структур данных ИЗ ФАЙЛА
        if not hasattr(farm_money, 'user_balances'):
            farm_money.user_balances = user_data.get("balances", {})
        if not hasattr(farm_money, 'last_used'):
            farm_money.last_used = user_data.get("last_used", {})
        
        # Обновляем активность пользователя
        user_id = message.from_user.id
        if user_id not in user_activity:
            user_activity[user_id] = 0
        user_activity[user_id] += 1
        
        # Обновляем активность чата
        if message.chat.type in ['group', 'supergroup']:
            chat_last_activity[message.chat.id] = time.time()
        
        current_time = time.time()
        
        # Проверка кд
        if user_id in farm_money.last_used:
            time_passed = current_time - farm_money.last_used[user_id]
            if time_passed < 240:
                remaining_time = 240 - int(time_passed)
                bot.reply_to(message, f"❌вы сможете использовать команду повторно через {remaining_time} секунд❌")
                return
        
        # Начисление денег
        farmed_amount = random.randint(800, 1900)
        
        if user_id not in farm_money.user_balances:
            farm_money.user_balances[user_id] = 0
        
        # Обновляем баланс
        new_balance = farm_money.user_balances[user_id] + farmed_amount
        if new_balance > 60000:
            new_balance = 60000
            farmed_amount = 60000 - farm_money.user_balances[user_id]
        
        farm_money.user_balances[user_id] = new_balance
        farm_money.last_used[user_id] = current_time
        
        # СОХРАНЯЕМ ДАННЫЕ ПОСЛЕ ИЗМЕНЕНИЯ
        save_user_data()
        
        response_text = f"🤑вы успешно нафармили деньги на flipper zero, вам было зачисленно {farmed_amount}₽, ваш баланс {new_balance}₽/60000₽🤑"
        bot.reply_to(message, response_text)
    except Exception as e:
        print(f"❌ Ошибка в /farma: {e}")

# Приветствие при добавлении бота в группу
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    try:
        for new_member in message.new_chat_members:
            if new_member.id == bot.get_me().id:
                welcome_text = "Здарова! напиши команду /farma чтобы начать фармить на великий flipper"
                bot.send_message(message.chat.id, welcome_text)
                chat_last_activity[message.chat.id] = time.time()
                break
    except Exception as e:
        print(f"❌ Ошибка в приветствии: {e}")

# Обновляем активность при любой команде в групповом чате
@bot.message_handler(func=lambda message: True)
def update_activity(message):
    try:
        if message.chat.type in ['group', 'supergroup']:
            chat_last_activity[message.chat.id] = time.time()
    except Exception as e:
        print(f"❌ Ошибка в обновлении активности: {e}")

# Запуск бота
if __name__ == "__main__":
    print("🤖 Бот Minerdodster203 запускается...")
    
    while True:
        try:
            print("🔗 Подключаемся к Telegram API...")
            bot.polling(
                none_stop=True,
                timeout=30,
                long_polling_timeout=30
            )
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Ошибка подключения: {e}")
            print("🔄 Перезапуск через 15 секунд...")
            time.sleep(15)
        except Exception as e:
            print(f"❌ Неизвестная ошибка: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)