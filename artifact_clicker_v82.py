# -*- coding: utf-8 -*-
"""
ARTIFACT CLICKER v8.2
Telegram bot game — Python + pyTelegramBotAPI + SQLite

Новая база данных: game.db
Если нужна полная очистка — удалите game.db перед запуском.
"""

import os
import time
import random
import sqlite3
import threading
from datetime import datetime, timedelta

import telebot
from telebot import types

# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_НОВЫЙ_ТОКЕН_СЮДА")

if not TOKEN or TOKEN == "ВСТАВЬ_НОВЫЙ_ТОКЕН_СЮДА":
    raise RuntimeError(
        "Вставь НОВЫЙ токен Telegram-бота в переменную TOKEN "
        "или задай BOT_TOKEN."
    )

DB_PATH = "game_v82.db"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DB_LOCK = threading.RLock()
USER_COOLDOWN = {}
USER_COOLDOWN_LOCK = threading.Lock()

# ============================================================
# GAME DATA
# ============================================================

RARITIES = {
    "Обычный": {"weight": 600, "mult": 1.00, "emoji": "⚪"},
    "Редкий": {"weight": 250, "mult": 1.45, "emoji": "🔵"},
    "Эпический": {"weight": 100, "mult": 2.10, "emoji": "🟣"},
    "Легендарный": {"weight": 40, "mult": 3.20, "emoji": "🟠"},
    "Мифический": {"weight": 10, "mult": 5.00, "emoji": "🔴"},
}

SLOTS = [
    ("weapon", "🗡", "Оружие"),
    ("armor", "🛡", "Броня"),
    ("amulet", "💍", "Амулет"),
    ("relic", "🔮", "Реликвия"),
    ("ring", "💎", "Кольцо"),
    ("artifact", "🌟", "Артефакт"),
]

THEMES = {
    "Лес": "🌲",
    "Огонь": "🔥",
    "Лёд": "❄️",
    "Океан": "🌊",
    "Магия": "🪄",
    "Бездны": "🌑",
    "Небо": "☀️",
    "Гроза": "⚡",
    "Проклятие": "☠️",
    "Древность": "🏺",
    "Технологии": "🤖",
    "Королевство": "👑",
    "Космос": "🌌",
    "Драконы": "🐉",
    "Апокалипсис": "💀",
}

# 15 тематических кейсов
CASES = [
    ("forest", "🌲 Лесной кейс", 50, "Лес"),
    ("fire", "🔥 Огненный кейс", 150, "Огонь"),
    ("ice", "❄️ Ледяной кейс", 250, "Лёд"),
    ("ocean", "🌊 Океанский кейс", 400, "Океан"),
    ("magic", "🪄 Магический кейс", 650, "Магия"),
    ("void", "🌑 Кейс Бездны", 1000, "Бездны"),
    ("sky", "☀️ Небесный кейс", 1500, "Небо"),
    ("storm", "⚡ Грозовой кейс", 2200, "Гроза"),
    ("curse", "☠️ Проклятый кейс", 3000, "Проклятие"),
    ("ancient", "🏺 Древний кейс", 4500, "Древность"),
    ("tech", "🤖 Технологический кейс", 6500, "Технологии"),
    ("royal", "👑 Королевский кейс", 9000, "Королевство"),
    ("cosmic", "🌌 Космический кейс", 13000, "Космос"),
    ("dragon", "🐉 Драконий кейс", 20000, "Драконы"),
    ("apocalypse", "💀 Апокалипсис", 35000, "Апокалипсис"),
    ("forest_elite", "🌳 Древний лес", 75000, "Лес"),
    ("fire_core", "🌋 Ядро вулкана", 110000, "Огонь"),
    ("ice_zero", "🧊 Абсолютный лёд", 160000, "Лёд"),
    ("ocean_abyss", "🐋 Бездна океана", 230000, "Океан"),
    ("magic_arcane", "🔮 Арканный кейс", 320000, "Магия"),
    ("void_singularity", "🕳 Сингулярность", 450000, "Бездны"),
    ("sky_celestial", "🌠 Небесный предел", 620000, "Небо"),
    ("storm_tempest", "⛈ Сердце бури", 850000, "Гроза"),
    ("curse_king", "☠️ Король проклятий", 1200000, "Проклятие"),
    ("ancient_god", "🏺 Божественная реликвия", 1700000, "Древность"),
    ("tech_quantum", "🤖 Квантовый модуль", 2400000, "Технологии"),
    ("royal_imperial", "👑 Императорский кейс", 3400000, "Королевство"),
    ("cosmic_nebula", "🌌 Туманность", 4800000, "Космос"),
    ("dragon_king", "🐲 Король драконов", 7000000, "Драконы"),
    ("apocalypse_last", "☠️ Последний день", 10000000, "Апокалипсис"),
]

ARTIFACTS = [
    # name, theme, slot, base_power, base_luck, crit, energy, rarity
    ("Древний лист", "Лес", "relic", 1, 1, 0, 0, "Обычный"),
    ("Корень титана", "Лес", "armor", 2, 2, 1, 1, "Редкий"),
    ("Сердце вулкана", "Огонь", "weapon", 5, 1, 2, 0, "Эпический"),
    ("Клинок пламени", "Огонь", "weapon", 8, 2, 3, 0, "Легендарный"),
    ("Ледяная корона", "Лёд", "armor", 4, 5, 1, 3, "Эпический"),
    ("Кристалл прилива", "Океан", "amulet", 3, 6, 0, 5, "Редкий"),
    ("Мана-кристалл", "Магия", "relic", 4, 4, 2, 4, "Редкий"),
    ("Посох архимага", "Магия", "weapon", 10, 8, 4, 2, "Легендарный"),
    ("Око Бездны", "Бездны", "amulet", 13, 10, 5, 0, "Мифический"),
    ("Солнечный медальон", "Небо", "amulet", 7, 7, 3, 5, "Легендарный"),
    ("Молот грома", "Гроза", "weapon", 12, 4, 6, 0, "Легендарный"),
    ("Проклятая маска", "Проклятие", "armor", 14, 12, 5, -2, "Мифический"),
    ("Реликвия царя", "Древность", "relic", 9, 9, 4, 4, "Легендарный"),
    ("Нейроядро", "Технологии", "ring", 11, 11, 4, 7, "Мифический"),
    ("Королевский перстень", "Королевство", "ring", 8, 14, 3, 5, "Легендарный"),
    ("Звезда коллапса", "Космос", "artifact", 20, 15, 8, 5, "Мифический"),
    ("Сердце дракона", "Драконы", "weapon", 22, 8, 9, 2, "Мифический"),
    ("Осколок конца", "Апокалипсис", "artifact", 28, 20, 10, -3, "Мифический"),
]

CASE_MAP = {c[0]: c for c in CASES}
ART_MAP = {a[0]: a for a in ARTIFACTS}
ARTIFACTS.extend([
    ("Лук зелёного духа", "Лес", "weapon", 7, 5, 2, 1, "Эпический"),
    ("Доспех лесного стража", "Лес", "armor", 6, 7, 1, 5, "Эпический"),
    ("Семя мирового дерева", "Лес", "artifact", 12, 10, 4, 8, "Легендарный"),
    ("Копьё лавы", "Огонь", "weapon", 14, 3, 5, 0, "Легендарный"),
    ("Панцирь лавового голема", "Огонь", "armor", 10, 4, 3, -1, "Эпический"),
    ("Печать сверхновой", "Огонь", "artifact", 20, 12, 8, 1, "Мифический"),
    ("Морозный клинок", "Лёд", "weapon", 13, 6, 5, 2, "Легендарный"),
    ("Броня вечной мерзлоты", "Лёд", "armor", 9, 10, 2, 8, "Легендарный"),
    ("Сердце ледяного титана", "Лёд", "artifact", 21, 14, 7, 10, "Мифический"),
    ("Трезубец прилива", "Океан", "weapon", 11, 10, 4, 6, "Легендарный"),
    ("Панцирь глубин", "Океан", "armor", 12, 8, 3, 9, "Эпический"),
    ("Жемчужина бездны", "Океан", "artifact", 19, 18, 6, 12, "Мифический"),
    ("Кинжал маны", "Магия", "weapon", 9, 13, 5, 6, "Легендарный"),
    ("Мантия архимага", "Магия", "armor", 8, 16, 3, 10, "Легендарный"),
    ("Гримуар бесконечности", "Магия", "artifact", 24, 20, 9, 12, "Мифический"),
    ("Коса пустоты", "Бездны", "weapon", 19, 11, 8, 0, "Мифический"),
    ("Плащ бездны", "Бездны", "armor", 15, 15, 5, 2, "Мифический"),
    ("Сфера сингулярности", "Бездны", "artifact", 30, 24, 12, 4, "Мифический"),
    ("Копьё света", "Небо", "weapon", 15, 12, 6, 7, "Легендарный"),
    ("Крылья рассвета", "Небо", "armor", 10, 17, 4, 12, "Легендарный"),
    ("Осколок солнца", "Небо", "artifact", 27, 23, 10, 15, "Мифический"),
    ("Меч молнии", "Гроза", "weapon", 18, 7, 10, 2, "Мифический"),
    ("Кираса громовержца", "Гроза", "armor", 14, 9, 6, 6, "Легендарный"),
    ("Ядро шторма", "Гроза", "artifact", 29, 19, 13, 8, "Мифический"),
    ("Катана проклятого", "Проклятие", "weapon", 21, 10, 10, -1, "Мифический"),
    ("Шлем проклятого воина", "Проклятие", "armor", 18, 14, 7, -2, "Мифический"),
    ("Сердце проклятия", "Проклятие", "artifact", 32, 22, 14, -3, "Мифический"),
    ("Меч императора", "Древность", "weapon", 17, 14, 7, 8, "Легендарный"),
    ("Доспех древнего царя", "Древность", "armor", 16, 13, 6, 9, "Легендарный"),
    ("Корона тысячелетия", "Древность", "artifact", 28, 25, 11, 14, "Мифический"),
    ("Плазменный клинок", "Технологии", "weapon", 23, 12, 9, 5, "Мифический"),
    ("Наноброня", "Технологии", "armor", 20, 16, 7, 15, "Мифический"),
    ("Квантовый процессор", "Технологии", "artifact", 31, 27, 12, 18, "Мифический"),
    ("Королевский меч", "Королевство", "weapon", 19, 18, 8, 9, "Мифический"),
    ("Императорская броня", "Королевство", "armor", 19, 19, 8, 13, "Мифический"),
    ("Королевский герб", "Королевство", "artifact", 30, 29, 12, 16, "Мифический"),
    ("Луч звезды", "Космос", "weapon", 25, 20, 11, 8, "Мифический"),
    ("Скафандр сингулярности", "Космос", "armor", 22, 21, 8, 17, "Мифический"),
    ("Глаз галактики", "Космос", "artifact", 36, 32, 15, 20, "Мифический"),
    ("Коготь дракона", "Драконы", "weapon", 28, 12, 13, 4, "Мифический"),
    ("Чешуя древнего дракона", "Драконы", "armor", 25, 15, 10, 12, "Мифический"),
    ("Душа дракона", "Драконы", "artifact", 40, 26, 17, 10, "Мифический"),
    ("Меч конца света", "Апокалипсис", "weapon", 32, 18, 15, -2, "Мифический"),
    ("Броня последнего выжившего", "Апокалипсис", "armor", 28, 20, 11, 5, "Мифический"),
    ("Сфера конца", "Апокалипсис", "artifact", 45, 35, 20, -5, "Мифический"),
])

ART_BY_NAME = {a[0]: a for a in ARTIFACTS}

POTIONS = {
    "luck": ("🧪 Зелье удачи", 300, "luck", 25, 600),
    "coins": ("💰 Золотое зелье", 500, "coins", 100, 300),
    "energy": ("⚡ Энергетик", 350, "energy", 50, 900),
    "xp": ("⭐ Зелье опыта", 450, "xp", 100, 600),
}

ACHIEVEMENTS = [
    ("first_tap", "⚔️ Первый тап", "Сделать 1 тап", "clicks", 1, 100, 20),
    ("click_100", "⚔️ Ученик клика", "Сделать 100 тапов", "clicks", 100, 300, 50),
    ("click_1000", "🔥 Мастер клика", "Сделать 1000 тапов", "clicks", 1000, 1500, 150),
    ("click_10000", "⚡ Машина кликов", "Сделать 10000 тапов", "clicks", 10000, 10000, 500),
    ("cases_10", "📦 Коллекционер", "Открыть 10 кейсов", "cases", 10, 1000, 100),
    ("cases_100", "🎰 Зависимость от кейсов", "Открыть 100 кейсов", "cases", 100, 10000, 500),
    ("level_10", "⭐ Десятый уровень", "Достичь 10 уровня", "level", 10, 5000, 250),
    ("coins_10000", "💰 Богач", "Накопить 10000 монет", "coins", 10000, 5000, 300),
    ("collection_10", "📚 Архивариус", "Собрать 10 разных артефактов", "collection", 10, 7000, 350),
    ("legendary", "🟠 Легенда", "Получить легендарный артефакт", "rarity", 4, 3000, 200),
    ("mythic", "🔴 Миф", "Получить мифический артефакт", "rarity", 5, 15000, 1000),
    ("raid_100", "👹 Охотник", "Нанести 100 урона рейдам", "raid", 100, 3000, 200),
]

# ============================================================
# DATABASE
# ============================================================

def db():
    conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def execute(sql, params=(), fetchone=False, fetchall=False, commit=True):
    with DB_LOCK:
        conn = db()
        try:
            cur = conn.execute(sql, params)
            if commit:
                conn.commit()
            if fetchone:
                return cur.fetchone()
            if fetchall:
                return cur.fetchall()
            return cur.lastrowid
        finally:
            conn.close()

def init_database():
    with DB_LOCK:
        conn = db()
        try:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                coins INTEGER NOT NULL DEFAULT 100,
                energy INTEGER NOT NULL DEFAULT 100,
                max_energy INTEGER NOT NULL DEFAULT 100,
                base_power INTEGER NOT NULL DEFAULT 1,
                base_luck INTEGER NOT NULL DEFAULT 5,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                prestige INTEGER NOT NULL DEFAULT 0,
                total_clicks INTEGER NOT NULL DEFAULT 0,
                total_cases INTEGER NOT NULL DEFAULT 0,
                raid_damage INTEGER NOT NULL DEFAULT 0,
                daily_streak INTEGER NOT NULL DEFAULT 0,
                last_bonus TEXT DEFAULT '',
                last_daily TEXT DEFAULT '',
                last_energy INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                artifact TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                equipped_slot TEXT DEFAULT '',
                obtained_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS collection (
                user_id INTEGER NOT NULL,
                artifact TEXT NOT NULL,
                first_found TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, artifact),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER NOT NULL,
                achievement TEXT NOT NULL,
                claimed INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(user_id, achievement),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS materials (
                user_id INTEGER PRIMARY KEY,
                wood INTEGER NOT NULL DEFAULT 0,
                iron INTEGER NOT NULL DEFAULT 0,
                crystal INTEGER NOT NULL DEFAULT 0,
                essence INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS potions (
                user_id INTEGER NOT NULL,
                potion TEXT NOT NULL,
                amount INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(user_id, potion),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS effects (
                user_id INTEGER PRIMARY KEY,
                luck_until INTEGER DEFAULT 0,
                luck_bonus INTEGER DEFAULT 0,
                coins_until INTEGER DEFAULT 0,
                coins_mult INTEGER DEFAULT 100,
                energy_until INTEGER DEFAULT 0,
                energy_bonus INTEGER DEFAULT 0,
                xp_until INTEGER DEFAULT 0,
                xp_bonus INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS states (
                user_id INTEGER PRIMARY KEY,
                mode TEXT DEFAULT '',
                payload TEXT DEFAULT '',
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS shop (
                id INTEGER PRIMARY KEY,
                item_type TEXT NOT NULL,
                item_key TEXT NOT NULL,
                price INTEGER NOT NULL,
                amount INTEGER NOT NULL DEFAULT 1,
                stock INTEGER NOT NULL DEFAULT 10
            );

            CREATE TABLE IF NOT EXISTS raid (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                max_hp INTEGER NOT NULL,
                hp INTEGER NOT NULL,
                ends_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS raid_hits (
                raid_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                damage INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(raid_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS gifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                gift_type TEXT NOT NULL,
                item_id INTEGER DEFAULT 0,
                amount INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS daily_quests (
                user_id INTEGER PRIMARY KEY,
                day TEXT NOT NULL,
                clicks INTEGER NOT NULL DEFAULT 0,
                cases INTEGER NOT NULL DEFAULT 0,
                raid_damage INTEGER NOT NULL DEFAULT 0,
                claimed1 INTEGER NOT NULL DEFAULT 0,
                claimed2 INTEGER NOT NULL DEFAULT 0,
                claimed3 INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)
            conn.commit()

            # Начальный рейд
            row = conn.execute("SELECT id FROM raid WHERE id=1").fetchone()
            if not row:
                conn.execute(
                    "INSERT INTO raid(id,name,max_hp,hp,ends_at) VALUES(1,?,?,?,?)",
                    ("🐉 Древний Дракон", 500000, 500000,
                     int(time.time()) + 86400)
                )
            # Магазин
            count = conn.execute("SELECT COUNT(*) AS c FROM shop").fetchone()["c"]
            if count == 0:
                items = [
                    (1, "coins", "coins", 250, 500, 99),
                    (2, "material", "wood", 150, 10, 99),
                    (3, "material", "iron", 300, 10, 99),
                    (4, "material", "crystal", 500, 5, 99),
                    (5, "material", "essence", 1000, 2, 99),
                    (6, "potion", "luck", 300, 1, 20),
                    (7, "potion", "coins", 500, 1, 20),
                    (8, "potion", "energy", 350, 1, 20),
                    (9, "potion", "xp", 450, 1, 20),
                ]
                conn.executemany(
                    "INSERT INTO shop(id,item_type,item_key,price,amount,stock) VALUES(?,?,?,?,?,?)",
                    items
                )
                conn.commit()
        finally:
            conn.close()

# ============================================================
# HELPERS
# ============================================================

def now():
    return int(time.time())

def today():
    return datetime.now().strftime("%Y-%m-%d")

def fmt(n):
    return f"{int(n):,}".replace(",", " ")

def progress_bar(value, maximum, size=12):
    maximum = max(1, maximum)
    filled = max(0, min(size, int(value / maximum * size)))
    return "█" * filled + "░" * (size - filled)

def cooldown(user_id, key, seconds):
    current = time.monotonic()
    with USER_COOLDOWN_LOCK:
        k = (user_id, key)
        last = USER_COOLDOWN.get(k, 0)
        if current - last < seconds:
            return False
        USER_COOLDOWN[k] = current
        return True

def answer(call, text=""):
    try:
        bot.answer_callback_query(call.id, text)
    except Exception:
        pass

def edit_or_send(call, text, markup=None):
    try:
        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            reply_markup=markup
        )
    except Exception:
        try:
            bot.send_message(call.message.chat.id, text, reply_markup=markup)
        except Exception:
            pass

def main_markup():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("⚔️ ТАП", callback_data="tap"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"),
        types.InlineKeyboardButton("📦 Кейсы", callback_data="cases"),
        types.InlineKeyboardButton("🔨 Кузница", callback_data="forge"),
        types.InlineKeyboardButton("🏆 Рейтинги", callback_data="top"),
        types.InlineKeyboardButton("📜 Квесты", callback_data="quests"),
        types.InlineKeyboardButton("🏅 Достижения", callback_data="achievements"),
        types.InlineKeyboardButton("📚 Коллекция", callback_data="collection"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="bonus"),
        types.InlineKeyboardButton("👹 Рейд", callback_data="raid"),
        types.InlineKeyboardButton("🏪 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🎁 Подарки", callback_data="gifts"),
        types.InlineKeyboardButton("🧪 Зелья", callback_data="potions"),
    )
    return kb

def back_markup():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
    return kb

def ensure_user(tg_user):
    uid = tg_user.id
    username = tg_user.username or ""
    first = tg_user.first_name or ""
    with DB_LOCK:
        conn = db()
        try:
            row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            if not row:
                conn.execute(
                    """INSERT INTO users
                    (id,username,first_name,last_energy) VALUES(?,?,?,?)""",
                    (uid, username, first, 100)
                )
                conn.execute("INSERT INTO materials(user_id) VALUES(?)", (uid,))
                conn.execute("INSERT INTO effects(user_id) VALUES(?)", (uid,))
                conn.execute("INSERT INTO states(user_id) VALUES(?)", (uid,))
                conn.execute(
                    "INSERT INTO daily_quests(user_id,day) VALUES(?,?)",
                    (uid, today())
                )
                conn.commit()
            else:
                conn.execute(
                    "UPDATE users SET username=?, first_name=? WHERE id=?",
                    (username, first, uid)
                )
                # Энергия
                row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
                elapsed = max(0, now() - int(row["last_energy"] or now()))
                gained = elapsed // 3
                if gained > 0 and row["energy"] < row["max_energy"]:
                    energy = min(row["max_energy"], row["energy"] + gained)
                    conn.execute(
                        "UPDATE users SET energy=?,last_energy=? WHERE id=?",
                        (energy, now(), uid)
                    )
                elif gained > 0:
                    conn.execute("UPDATE users SET last_energy=? WHERE id=?", (now(), uid))

                q = conn.execute(
                    "SELECT day FROM daily_quests WHERE user_id=?", (uid,)
                ).fetchone()
                if not q:
                    conn.execute(
                        "INSERT INTO daily_quests(user_id,day) VALUES(?,?)",
                        (uid, today())
                    )
                elif q["day"] != today():
                    conn.execute("""
                        UPDATE daily_quests
                        SET day=?, clicks=0, cases=0, raid_damage=0,
                            claimed1=0, claimed2=0, claimed3=0
                        WHERE user_id=?
                    """, (today(), uid))
                conn.commit()
        finally:
            conn.close()
    return get_user(uid)

def get_user(uid):
    ensure_no_recursion = False
    with DB_LOCK:
        conn = db()
        try:
            row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            return row
        finally:
            conn.close()

def get_stats(uid):
    u = get_user(uid)
    if not u:
        return 1, 5, 0, 100, 0
    power = u["base_power"]
    luck = u["base_luck"]
    crit = 0
    energy_bonus = 0

    rows = execute(
        "SELECT artifact,level,equipped_slot FROM inventory WHERE user_id=? AND equipped_slot!=''",
        (uid,), fetchall=True
    )
    for r in rows:
        art = ART_BY_NAME.get(r["artifact"])
        if not art:
            continue
        name, theme, slot, bp, bl, bc, be, rarity = art
        mult = RARITIES[rarity]["mult"]
        lvl_mult = 1 + (r["level"] - 1) * 0.08
        power += int(bp * mult * lvl_mult)
        luck += int(bl * mult * lvl_mult)
        crit += int(bc * lvl_mult)
        energy_bonus += int(be * lvl_mult)

    eff = execute("SELECT * FROM effects WHERE user_id=?", (uid,), fetchone=True)
    if eff:
        ts = now()
        if eff["luck_until"] > ts:
            luck += eff["luck_bonus"]
        if eff["energy_until"] > ts:
            energy_bonus += eff["energy_bonus"]

    max_energy = 100 + (u["level"] - 1) * 5 + energy_bonus + u["prestige"] * 10
    return power, luck, crit, max_energy, energy_bonus

def xp_needed(level):
    return 100 + (level - 1) * 80 + (level - 1) ** 2 * 10

def add_xp(uid, amount):
    with DB_LOCK:
        conn = db()
        try:
            u = conn.execute("SELECT level,xp FROM users WHERE id=?", (uid,)).fetchone()
            if not u:
                return 0
            eff = conn.execute("SELECT * FROM effects WHERE user_id=?", (uid,)).fetchone()
            if eff and eff["xp_until"] > now():
                amount = int(amount * (100 + eff["xp_bonus"]) / 100)

            xp = u["xp"] + amount
            level = u["level"]
            gained_levels = 0
            while xp >= xp_needed(level):
                xp -= xp_needed(level)
                level += 1
                gained_levels += 1

            conn.execute(
                "UPDATE users SET xp=?,level=? WHERE id=?",
                (xp, level, uid)
            )
            if gained_levels:
                conn.execute(
                    "UPDATE users SET max_energy=max_energy+? WHERE id=?",
                    (gained_levels * 5, uid)
                )
            conn.commit()
            return gained_levels
        finally:
            conn.close()

def add_coins(uid, amount):
    with DB_LOCK:
        conn = db()
        try:
            eff = conn.execute("SELECT * FROM effects WHERE user_id=?", (uid,)).fetchone()
            if amount > 0 and eff and eff["coins_until"] > now():
                amount = int(amount * eff["coins_mult"] / 100)
            conn.execute(
                "UPDATE users SET coins=max(0,coins+?) WHERE id=?",
                (amount, uid)
            )
            conn.commit()
        finally:
            conn.close()

def add_material(uid, key, amount):
    if key not in ("wood", "iron", "crystal", "essence"):
        return
    execute(
        f"UPDATE materials SET {key}=max(0,{key}+?) WHERE user_id=?",
        (amount, uid)
    )

def rarity_roll(luck):
    # Удача слегка повышает редкости.
    base = [600, 250, 100, 40, 10]
    boost = min(80, max(0, luck - 5) * 3)
    weights = [
        max(100, base[0] - boost * 2),
        base[1] + boost,
        base[2] + boost,
        base[3] + int(boost * 0.7),
        base[4] + int(boost * 0.3),
    ]
    return random.choices(list(RARITIES.keys()), weights=weights, k=1)[0]

def artifact_for_case(theme, luck):
    candidates = [a for a in ARTIFACTS if a[1] == theme]
    if not candidates:
        candidates = ARTIFACTS
    rarity = rarity_roll(luck)
    same = [a for a in candidates if a[7] == rarity]
    if not same:
        # Берём ближайшую редкость, чтобы кейсы не были пустыми.
        same = candidates
    return random.choice(same)

def add_artifact(uid, artifact_name, level=1):
    with DB_LOCK:
        conn = db()
        try:
            cur = conn.execute(
                "INSERT INTO inventory(user_id,artifact,level,equipped_slot) VALUES(?,?,?,'')",
                (uid, artifact_name, level)
            )
            conn.execute(
                "INSERT OR IGNORE INTO collection(user_id,artifact) VALUES(?,?)",
                (uid, artifact_name)
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

def rarity_index(r):
    return list(RARITIES.keys()).index(r) + 1

def user_collection_count(uid):
    return execute(
        "SELECT COUNT(*) AS c FROM collection WHERE user_id=?",
        (uid,), fetchone=True
    )["c"]

def equipped_count(uid):
    return execute(
        "SELECT COUNT(*) AS c FROM inventory WHERE user_id=? AND equipped_slot!=''",
        (uid,), fetchone=True
    )["c"]

def equipped_slot_names(uid):
    rows = execute(
        "SELECT equipped_slot,artifact FROM inventory WHERE user_id=? AND equipped_slot!=''",
        (uid,), fetchall=True
    )
    return {r["equipped_slot"]: r["artifact"] for r in rows}

def sanitize_equipment(uid):
    # Страховка от старых/битых данных: максимум один предмет на слот и максимум 6 предметов.
    with DB_LOCK:
        conn = db()
        try:
            rows = conn.execute(
                "SELECT id,equipped_slot FROM inventory WHERE user_id=? AND equipped_slot!='' ORDER BY id",
                (uid,)
            ).fetchall()
            used = set()
            kept = 0
            for r in rows:
                slot = r["equipped_slot"]
                if slot not in dict((s[0], s[0]) for s in SLOTS) or slot in used or kept >= len(SLOTS):
                    conn.execute("UPDATE inventory SET equipped_slot='' WHERE id=?", (r["id"],))
                else:
                    used.add(slot)
                    kept += 1
            conn.commit()
        finally:
            conn.close()

# ============================================================
# TEXT SCREENS
# ============================================================

def home_text(uid):
    sanitize_equipment(uid)
    u = get_user(uid)
    power, luck, crit, max_energy, _ = get_stats(uid)
    energy = min(max_energy, u["energy"])
    bar = progress_bar(u["xp"], xp_needed(u["level"]))
    combo = get_combo(uid)

    return (
        "⚔️ <b>ARTIFACT CLICKER v8.2</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Монеты: <b>{fmt(u['coins'])}</b>\n"
        f"⚡ Энергия: <b>{energy}/{max_energy}</b>\n"
        f"🗡 Сила: <b>{power}</b>\n"
        f"🍀 Удача: <b>{luck}%</b>\n"
        f"💥 Крит: <b>{crit}%</b>\n"
        f"🔥 Комбо: <b>x{combo}</b>\n"
        f"⭐ Уровень: <b>{u['level']}</b>\n"
        f"📈 XP: {bar} {u['xp']}/{xp_needed(u['level'])}\n\n"
        "Нажимай <b>⚔️ ТАП</b>, открывай кейсы и собирай коллекцию."
    )

COMBOS = {}

def get_combo(uid):
    data = COMBOS.get(uid)
    if not data:
        return 0
    count, stamp = data
    if time.monotonic() - stamp > 4:
        COMBOS.pop(uid, None)
        return 0
    return count

def tap_user(uid):
    if not cooldown(uid, "tap", 0.22):
        return None

    with DB_LOCK:
        conn = db()
        try:
            u = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            if not u:
                return None
            power, luck, crit, max_energy, _ = get_stats(uid)
            energy = min(max_energy, u["energy"])
            if energy <= 0:
                return {"error": "energy"}

            energy -= 1
            combo = get_combo(uid) + 1
            COMBOS[uid] = (combo, time.monotonic())

            roll = random.randint(1, 100)
            if roll <= min(5, max(0, crit)):
                mult = 4
                kind = "💥 СУПЕР-КРИТ"
            elif roll <= min(50, max(0, crit + luck)):
                mult = 2
                kind = "⚡ КРИТ"
            else:
                mult = 1
                kind = "⚔️ ТАП"

            combo_bonus = min(2.0, 1 + combo * 0.01)
            coins = max(1, int(power * mult * combo_bonus))
            xp = max(1, int(3 * mult))

            conn.execute(
                """UPDATE users
                   SET coins=coins+?, energy=?, total_clicks=total_clicks+1,
                       last_energy=?
                   WHERE id=?""",
                (coins, energy, now(), uid)
            )
            conn.execute(
                "UPDATE daily_quests SET clicks=clicks+1 WHERE user_id=?",
                (uid,)
            )
            conn.commit()
        finally:
            conn.close()

    add_xp(uid, xp)

    # Случайная находка
    found = None
    if random.random() < 0.008:
        mat = random.choice(["wood", "iron", "crystal", "essence"])
        amount = random.randint(1, 3)
        add_material(uid, mat, amount)
        found = f"🎁 Найден ресурс: <b>{mat} +{amount}</b>"

    return {
        "coins": coins,
        "xp": xp,
        "kind": kind,
        "combo": combo,
        "found": found,
    }

def profile_text(uid):
    sanitize_equipment(uid)
    u = get_user(uid)
    power, luck, crit, max_energy, _ = get_stats(uid)
    inv = execute(
        "SELECT COUNT(*) AS c FROM inventory WHERE user_id=?", (uid,), fetchone=True
    )["c"]
    coll = user_collection_count(uid)
    ach = execute(
        "SELECT COUNT(*) AS c FROM achievements WHERE user_id=? AND claimed=1",
        (uid,), fetchone=True
    )["c"]
    name = ("@" + u["username"]) if u["username"] else u["first_name"] or str(uid)
    return (
        "👤 <b>ПРОФИЛЬ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 {name}\n"
        f"💰 Монеты: <b>{fmt(u['coins'])}</b>\n"
        f"⚡ Энергия: <b>{u['energy']}/{max_energy}</b>\n"
        f"⭐ Уровень: <b>{u['level']}</b>\n"
        f"♻️ Престиж: <b>{u['prestige']}</b>\n"
        f"🗡 Сила: <b>{power}</b>\n"
        f"🍀 Удача: <b>{luck}%</b>\n"
        f"💥 Крит: <b>{crit}%</b>\n"
        f"🎒 Артефактов: <b>{inv}</b>\n"
        f"📚 Коллекция: <b>{coll}/{len(ARTIFACTS)}</b>\n"
        f"🏅 Достижения: <b>{ach}/{len(ACHIEVEMENTS)}</b>\n"
        f"⚔️ Тапов: <b>{fmt(u['total_clicks'])}</b>\n"
        f"📦 Кейсов: <b>{fmt(u['total_cases'])}</b>\n"
        f"👹 Урон рейдам: <b>{fmt(u['raid_damage'])}</b>"
    )

def inventory_text(uid):
    sanitize_equipment(uid)
    rows = execute(
        "SELECT * FROM inventory WHERE user_id=? ORDER BY id DESC",
        (uid,), fetchall=True
    )
    slots = equipped_slot_names(uid)
    text = "🎒 <b>ИНВЕНТАРЬ</b>\n━━━━━━━━━━━━━━━━━━\n"
    text += f"⚔️ Экипировано: <b>{len(slots)}/{len(SLOTS)}</b>\n\n"

    if not rows:
        text += "Пока пусто. Открой первый кейс.\n"
    else:
        for r in rows[:30]:
            art = ART_BY_NAME.get(r["artifact"])
            if not art:
                continue
            name, theme, slot, bp, bl, bc, be, rarity = art
            eq = f" ⚔️ {r['equipped_slot']}" if r["equipped_slot"] else ""
            re = RARITIES[rarity]["emoji"]
            text += (
                f"{re} <b>#{r['id']} {name}</b> — {rarity}\n"
                f"   {THEMES.get(theme,'✨')} {theme} | Lv.{r['level']}{eq}\n"
                f"   🗡 +{bp}  🍀 +{bl}  💥 +{bc}%  ⚡ +{be}\n"
            )
    return text

def inventory_markup(uid):
    sanitize_equipment(uid)
    rows = execute(
        "SELECT * FROM inventory WHERE user_id=? ORDER BY id DESC LIMIT 30",
        (uid,), fetchall=True
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    for r in rows:
        art = ART_BY_NAME.get(r["artifact"])
        if not art:
            continue
        name = art[0]
        if r["equipped_slot"]:
            label = f"❌ Снять #{r['id']}"
        else:
            label = f"⚔️ Надеть #{r['id']}"
        kb.add(types.InlineKeyboardButton(
            label, callback_data=f"item:{r['id']}"
        ))
    kb.add(types.InlineKeyboardButton("🔨 Управление", callback_data="forge"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
    return kb

def cases_text(uid):
    u = get_user(uid)
    _, luck, _, _, _ = get_stats(uid)
    text = (
        "📦 <b>ТЕМАТИЧЕСКИЕ КЕЙСЫ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 Баланс: <b>{fmt(u['coins'])}</b>\n"
        f"🍀 Удача: <b>{luck}%</b>\n\n"
    )
    for key, name, price, theme in CASES:
        text += f"{THEMES.get(theme,'📦')} {name} — <b>{fmt(price)}💰</b>\n"
    return text

def cases_markup():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name, price, theme in CASES:
        kb.add(types.InlineKeyboardButton(
            f"{THEMES.get(theme,'📦')} {name.split(' ',1)[-1]} • {fmt(price)}",
            callback_data=f"case:{key}"
        ))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
    return kb

def collection_text(uid):
    found = {r["artifact"] for r in execute(
        "SELECT artifact FROM collection WHERE user_id=?", (uid,), fetchall=True
    )}
    by_theme = {}
    for a in ARTIFACTS:
        by_theme.setdefault(a[1], []).append(a)

    text = f"📚 <b>КОЛЛЕКЦИЯ {len(found)}/{len(ARTIFACTS)}</b>\n━━━━━━━━━━━━━━━━━━\n"
    for theme, arr in by_theme.items():
        count = sum(a[0] in found for a in arr)
        text += f"\n{THEMES.get(theme,'✨')} <b>{theme}</b> {count}/{len(arr)}\n"
        for a in arr:
            if a[0] in found:
                text += f"  ✅ {a[0]} — {a[7]}\n"
            else:
                text += "  🔒 ???\n"
    return text

def achievements_text(uid):
    u = get_user(uid)
    claimed = {
        r["achievement"] for r in execute(
            "SELECT achievement FROM achievements WHERE user_id=? AND claimed=1",
            (uid,), fetchall=True
        )
    }
    pending = {
        r["achievement"] for r in execute(
            "SELECT achievement FROM achievements WHERE user_id=? AND claimed=0",
            (uid,), fetchall=True
        )
    }
    text = "🏅 <b>ДОСТИЖЕНИЯ</b>\n━━━━━━━━━━━━━━━━━━\n"
    for key, name, desc, metric, target, coins, xp in ACHIEVEMENTS:
        if key in claimed:
            icon = "✅"
        elif key in pending:
            icon = "🎁"
        else:
            icon = "🔒"
        text += f"{icon} <b>{name}</b>\n   {desc} • +{coins}💰 +{xp}XP\n"
    return text

def check_achievements(uid):
    u = get_user(uid)
    coll = user_collection_count(uid)
    rows = execute(
        "SELECT artifact FROM inventory WHERE user_id=?", (uid,), fetchall=True
    )
    best_rarity = max(
        [rarity_index(ART_BY_NAME[r["artifact"]][7]) for r in rows if r["artifact"] in ART_BY_NAME],
        default=0
    )
    raid = u["raid_damage"]

    values = {
        "clicks": u["total_clicks"],
        "cases": u["total_cases"],
        "level": u["level"],
        "coins": u["coins"],
        "collection": coll,
        "rarity": best_rarity,
        "raid": raid,
    }

    newly = []
    for key, name, desc, metric, target, coins, xp in ACHIEVEMENTS:
        old = execute(
            "SELECT claimed FROM achievements WHERE user_id=? AND achievement=?",
            (uid, key), fetchone=True
        )
        if old:
            continue
        if values.get(metric, 0) >= target:
            execute(
                "INSERT OR REPLACE INTO achievements(user_id,achievement,claimed) VALUES(?,?,0)",
                (uid, key)
            )
            newly.append(name)
    return newly

def quests_text(uid):
    q = execute(
        "SELECT * FROM daily_quests WHERE user_id=?", (uid,), fetchone=True
    )
    text = (
        "📜 <b>ЕЖЕДНЕВНЫЕ КВЕСТЫ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ 100 тапов: <b>{min(q['clicks'],100)}/100</b> — 🎁 500💰\n"
        f"📦 3 кейса: <b>{min(q['cases'],3)}/3</b> — 🎁 3💎\n"
        f"👹 500 урона рейду: <b>{min(q['raid_damage'],500)}/500</b> — 🎁 5🟣\n"
    )
    return text

def quests_markup(uid):
    q = execute("SELECT * FROM daily_quests WHERE user_id=?", (uid,), fetchone=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    if q["clicks"] >= 100 and not q["claimed1"]:
        kb.add(types.InlineKeyboardButton("🎁 Забрать 500💰", callback_data="quest:1"))
    if q["cases"] >= 3 and not q["claimed2"]:
        kb.add(types.InlineKeyboardButton("🎁 Забрать 3💎", callback_data="quest:2"))
    if q["raid_damage"] >= 500 and not q["claimed3"]:
        kb.add(types.InlineKeyboardButton("🎁 Забрать 5🟣", callback_data="quest:3"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
    return kb

def bonus_text(uid):
    u = get_user(uid)
    ready = u["last_daily"] != today()
    return (
        "🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🔥 Серия: <b>{u['daily_streak']}</b>\n\n"
        + ("🟢 Бонус доступен!" if ready else "⏳ Бонус уже получен сегодня.")
    )

def forge_text(uid):
    rows = execute(
        "SELECT * FROM inventory WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (uid,), fetchall=True
    )
    text = (
        "🔨 <b>КУЗНИЦА</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Выбери артефакт для улучшения.\n\n"
    )
    for r in rows:
        art = ART_BY_NAME.get(r["artifact"])
        if art:
            text += f"#{r['id']} {art[0]} • Lv.{r['level']} • {art[7]}\n"
    return text

def forge_markup(uid):
    rows = execute(
        "SELECT * FROM inventory WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (uid,), fetchall=True
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    for r in rows:
        if r["equipped_slot"]:
            continue
        kb.add(types.InlineKeyboardButton(
            f"🔨 #{r['id']} Lv.{r['level']}",
            callback_data=f"upgrade:{r['id']}"
        ))
    kb.add(types.InlineKeyboardButton("♻️ Престиж", callback_data="prestige"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
    return kb

def shop_text(uid):
    rows = execute("SELECT * FROM shop ORDER BY id", fetchall=True)
    u = get_user(uid)
    return (
        "🏪 <b>МАГАЗИН</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 Баланс: <b>{fmt(u['coins'])}</b>\n\n"
        + "\n".join(
            f"#{r['id']} • {shop_name(r['item_type'],r['item_key'],r['amount'])} — {fmt(r['price'])}💰"
            for r in rows if r["stock"] > 0
        )
    )

def shop_name(item_type, key, amount):
    if item_type == "coins":
        return f"💰 +{amount} монет"
    if item_type == "material":
        return f"🔹 {key} +{amount}"
    if item_type == "potion":
        return POTIONS[key][0]
    return key

def shop_markup():
    rows = execute("SELECT * FROM shop ORDER BY id", fetchall=True)
    kb = types.InlineKeyboardMarkup(row_width=2)
    for r in rows:
        if r["stock"] <= 0:
            continue
        kb.add(types.InlineKeyboardButton(
            f"🛒 #{r['id']} • {r['price']}💰",
            callback_data=f"buy:{r['id']}"
        ))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
    return kb

def potions_text(uid):
    rows = execute(
        "SELECT potion,amount FROM potions WHERE user_id=? AND amount>0",
        (uid,), fetchall=True
    )
    text = "🧪 <b>ЗЕЛЬЯ</b>\n━━━━━━━━━━━━━━━━━━\n"
    if not rows:
        text += "У тебя пока нет зелий.\nКупить их можно в магазине."
    else:
        for r in rows:
            text += f"{POTIONS[r['potion']][0]} ×{r['amount']}\n"
    return text

def potions_markup(uid):
    rows = execute(
        "SELECT potion,amount FROM potions WHERE user_id=? AND amount>0",
        (uid,), fetchall=True
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    for r in rows:
        kb.add(types.InlineKeyboardButton(
            f"🧪 Использовать {r['potion']} ×{r['amount']}",
            callback_data=f"potion:{r['potion']}"
        ))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
    return kb

def raid_text(uid):
    raid = execute("SELECT * FROM raid WHERE id=1", fetchone=True)
    if raid["ends_at"] <= now() or raid["hp"] <= 0:
        return "👹 <b>РЕЙД ЗАВЕРШЁН</b>\n\nНовый босс появится автоматически при следующем открытии."
    hit = execute(
        "SELECT damage FROM raid_hits WHERE raid_id=1 AND user_id=?",
        (uid,), fetchone=True
    )
    personal = hit["damage"] if hit else 0
    remaining = max(0, raid["ends_at"] - now())
    phase = "🟢 I" if raid["hp"] > raid["max_hp"] * 0.66 else ("🟡 II" if raid["hp"] > raid["max_hp"] * 0.33 else "🔴 III")
    hours = remaining // 3600
    minutes = (remaining % 3600) // 60
    return (
        f"{raid['name']} <b>РЕЙД</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"❤️ HP: <b>{fmt(raid['hp'])}/{fmt(raid['max_hp'])}</b>\n"
        f"🔥 Фаза босса: <b>{phase}</b>\n"
        f"📊 {progress_bar(raid['max_hp']-raid['hp'],raid['max_hp'],16)}\n"
        f"⏱ Осталось: <b>{hours:02d}:{minutes:02d}</b>\n"
        f"⚔️ Твой урон: <b>{fmt(personal)}</b>\n\n"
        "Нажимай кнопку атаки. Урон зависит от твоей силы."
    )

def raid_markup():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⚔️ АТАКОВАТЬ БОССА", callback_data="raid_hit"))
    kb.add(types.InlineKeyboardButton("🏆 Топ рейда", callback_data="raid_top"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
    return kb

def top_text(uid):
    rows = execute(
        """SELECT username,first_name,coins,total_clicks,level,prestige,raid_damage
           FROM users ORDER BY coins DESC LIMIT 10""",
        fetchall=True
    )
    text = "🏆 <b>РЕЙТИНГИ</b>\n━━━━━━━━━━━━━━━━━━\n\n"
    text += "<b>💰 Богачи</b>\n"
    for i, r in enumerate(rows, 1):
        name = ("@" + r["username"]) if r["username"] else (r["first_name"] or str(i))
        text += f"{i}. {name} — {fmt(r['coins'])}💰\n"
    text += "\n<b>👹 Рейтинг рейда</b>\n"
    raidrows = execute(
        """SELECT u.username,u.first_name,h.damage
           FROM raid_hits h JOIN users u ON u.id=h.user_id
           WHERE h.raid_id=1 ORDER BY h.damage DESC LIMIT 10""",
        fetchall=True
    )
    for i, r in enumerate(raidrows, 1):
        name = ("@" + r["username"]) if r["username"] else (r["first_name"] or str(i))
        text += f"{i}. {name} — {fmt(r['damage'])}\n"
    return text

def gifts_text(uid):
    return (
        "🎁 <b>ПОДАРКИ И ПЕРЕВОДЫ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Чтобы подарить артефакт:\n"
        "<code>/gift @username ID</code>\n"
        "где ID — номер предмета из инвентаря.\n\n"
        "Чтобы передать монеты:\n"
        "<code>/pay @username сумма</code>\n\n"
        "Пример:\n"
        "<code>/gift @player 17</code>\n"
        "<code>/pay @player 500</code>\n\n"
        "Экипированные артефакты передавать нельзя."
    )

# ============================================================
# COMMANDS
# ============================================================

@bot.message_handler(commands=["start"])
def cmd_start(message):
    ensure_user(message.from_user)
    bot.send_message(
        message.chat.id,
        home_text(message.from_user.id),
        reply_markup=main_markup()
    )

@bot.message_handler(commands=["gift"])
def cmd_gift(message):
    ensure_user(message.from_user)
    parts = message.text.split()
    if len(parts) != 3 or not parts[1].startswith("@"):
        bot.reply_to(message, "Формат: <code>/gift @username ID</code>")
        return
    target_name = parts[1][1:].lower()
    try:
        item_id = int(parts[2])
    except ValueError:
        bot.reply_to(message, "ID артефакта должен быть числом.")
        return
    sender = message.from_user.id
    if not cooldown(sender, "gift", 1.5):
        return

    target = execute(
        "SELECT id FROM users WHERE lower(username)=?",
        (target_name,), fetchone=True
    )
    if not target:
        bot.reply_to(message, "Игрок с таким @username не найден. Он должен хотя бы один раз запустить бота.")
        return
    if target["id"] == sender:
        bot.reply_to(message, "Нельзя подарить артефакт самому себе.")
        return

    with DB_LOCK:
        conn = db()
        try:
            item = conn.execute(
                "SELECT * FROM inventory WHERE id=? AND user_id=?",
                (item_id, sender)
            ).fetchone()
            if not item:
                bot.reply_to(message, "Такого артефакта нет в твоём инвентаре.")
                return
            if item["equipped_slot"]:
                bot.reply_to(message, "Сначала сними этот артефакт.")
                return
            conn.execute(
                "UPDATE inventory SET user_id=?, equipped_slot='' WHERE id=?",
                (target["id"], item_id)
            )
            conn.execute(
                "INSERT OR IGNORE INTO collection(user_id,artifact) VALUES(?,?)",
                (target["id"], item["artifact"])
            )
            conn.execute(
                "INSERT INTO gifts(sender_id,receiver_id,gift_type,item_id,amount) VALUES(?,?,?,?,?)",
                (sender,target["id"],"artifact",item_id,0)
            )
            conn.commit()
        finally:
            conn.close()

    bot.reply_to(message, f"🎁 Артефакт #{item_id} подарен игроку @{target_name}.")
    try:
        bot.send_message(target["id"], f"🎁 Тебе подарили артефакт <b>#{item_id}</b>!")
    except Exception:
        pass

@bot.message_handler(commands=["pay"])
def cmd_pay(message):
    ensure_user(message.from_user)
    parts = message.text.split()
    if len(parts) != 3 or not parts[1].startswith("@"):
        bot.reply_to(message, "Формат: <code>/pay @username сумма</code>")
        return
    target_name = parts[1][1:].lower()
    try:
        amount = int(parts[2])
    except ValueError:
        bot.reply_to(message, "Сумма должна быть числом.")
        return
    if amount <= 0 or amount > 1_000_000:
        bot.reply_to(message, "Сумма должна быть от 1 до 1 000 000.")
        return
    sender = message.from_user.id
    if not cooldown(sender, "pay", 1.5):
        return
    target = execute(
        "SELECT id FROM users WHERE lower(username)=?",
        (target_name,), fetchone=True
    )
    if not target:
        bot.reply_to(message, "Игрок не найден.")
        return
    if target["id"] == sender:
        bot.reply_to(message, "Нельзя переводить монеты самому себе.")
        return

    with DB_LOCK:
        conn = db()
        try:
            u = conn.execute("SELECT coins FROM users WHERE id=?", (sender,)).fetchone()
            if u["coins"] < amount:
                bot.reply_to(message, "Недостаточно монет.")
                return
            conn.execute("UPDATE users SET coins=coins-? WHERE id=?", (amount,sender))
            conn.execute("UPDATE users SET coins=coins+? WHERE id=?", (amount,target["id"]))
            conn.execute(
                "INSERT INTO gifts(sender_id,receiver_id,gift_type,amount) VALUES(?,?,?,?)",
                (sender,target["id"],"coins",amount)
            )
            conn.commit()
        finally:
            conn.close()
    bot.reply_to(message, f"💰 Переведено {fmt(amount)} монет игроку @{target_name}.")
    try:
        bot.send_message(target["id"], f"💰 Тебе перевели <b>{fmt(amount)}</b> монет.")
    except Exception:
        pass

# ============================================================
# CALLBACK ROUTER
# ============================================================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    uid = call.from_user.id
    ensure_user(call.from_user)
    data = call.data

    if data == "tap":
        result = tap_user(uid)
        if result is None:
            answer(call, "Слишком быстро.")
            return
        if result.get("error") == "energy":
            answer(call, "⚡ Энергия закончилась.")
            edit_or_send(call, home_text(uid), main_markup())
            return

        check_achievements(uid)
        msg = (
            f"{result['kind']} <b>+{result['coins']}💰</b> | "
            f"+{result['xp']} XP | 🔥 x{result['combo']}"
        )
        if result["found"]:
            msg += "\n" + result["found"]
        answer(call, msg[:180])
        edit_or_send(call, home_text(uid) + "\n\n" + msg, main_markup())
        return

    if data == "home":
        answer(call)
        edit_or_send(call, home_text(uid), main_markup())
        return

    if data == "profile":
        answer(call)
        edit_or_send(call, profile_text(uid), back_markup())
        return

    if data == "inventory":
        answer(call)
        edit_or_send(call, inventory_text(uid), inventory_markup(uid))
        return

    if data == "cases":
        answer(call)
        edit_or_send(call, cases_text(uid), cases_markup())
        return

    if data == "collection":
        answer(call)
        edit_or_send(call, collection_text(uid), back_markup())
        return

    if data == "achievements":
        answer(call)
        check_achievements(uid)
        kb = types.InlineKeyboardMarkup()
        rows = execute(
            "SELECT achievement FROM achievements WHERE user_id=? AND claimed=0",
            (uid,), fetchall=True
        )
        for r in rows:
            kb.add(types.InlineKeyboardButton(
                f"🎁 Забрать: {r['achievement']}",
                callback_data=f"ach:{r['achievement']}"
            ))
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
        edit_or_send(call, achievements_text(uid), kb)
        return

    if data.startswith("ach:"):
        key = data.split(":",1)[1]
        if not cooldown(uid, "ach", 0.4):
            answer(call, "Подожди.")
            return
        check_achievements(uid)
        row = execute(
            "SELECT claimed FROM achievements WHERE user_id=? AND achievement=?",
            (uid,key), fetchone=True
        )
        if not row or row["claimed"]:
            answer(call, "Награда уже забрана.")
            return
        ach = next((a for a in ACHIEVEMENTS if a[0] == key), None)
        if not ach:
            answer(call, "Ошибка.")
            return
        execute(
            "UPDATE achievements SET claimed=1 WHERE user_id=? AND achievement=?",
            (uid,key)
        )
        add_coins(uid, ach[5])
        add_xp(uid, ach[6])
        answer(call, f"🎁 +{ach[5]}💰 +{ach[6]} XP")
        edit_or_send(call, achievements_text(uid), back_markup())
        return

    if data == "quests":
        answer(call)
        edit_or_send(call, quests_text(uid), quests_markup(uid))
        return

    if data.startswith("quest:"):
        qid = int(data.split(":")[1])
        if not cooldown(uid, "quest", 0.5):
            answer(call, "Подожди.")
            return
        q = execute("SELECT * FROM daily_quests WHERE user_id=?", (uid,), fetchone=True)
        field = {1:"claimed1",2:"claimed2",3:"claimed3"}[qid]
        complete = {
            1: q["clicks"] >= 100,
            2: q["cases"] >= 3,
            3: q["raid_damage"] >= 500
        }[qid]
        if q[field] or not complete:
            answer(call, "Награда пока недоступна.")
            return
        execute(f"UPDATE daily_quests SET {field}=1 WHERE user_id=?", (uid,))
        if qid == 1:
            add_coins(uid, 500)
            answer(call, "🎁 +500 монет")
        elif qid == 2:
            add_material(uid, "crystal", 3)
            answer(call, "🎁 +3 кристалла")
        else:
            add_material(uid, "essence", 5)
            answer(call, "🎁 +5 эссенции")
        edit_or_send(call, quests_text(uid), quests_markup(uid))
        return

    if data.startswith("case:"):
        key = data.split(":",1)[1]
        if not cooldown(uid, "case", 0.5):
            answer(call, "⏳ Не так быстро.")
            return
        case = CASE_MAP.get(key)
        if not case:
            answer(call, "Кейс не найден.")
            return
        _, name, price, theme = case
        u = get_user(uid)
        if u["coins"] < price:
            answer(call, "💰 Не хватает монет.")
            return
        _, luck, _, _, _ = get_stats(uid)
        artifact = artifact_for_case(theme, luck)
        add_id = add_artifact(uid, artifact[0])

        material = random.choice(["wood","iron","crystal","essence"])
        mat_amount = max(1, price // 1000)
        if artifact[7] == "Мифический":
            mat_amount += 3
        with DB_LOCK:
            conn = db()
            try:
                conn.execute("UPDATE users SET coins=coins-?,total_cases=total_cases+1 WHERE id=?", (price,uid))
                conn.execute("UPDATE daily_quests SET cases=cases+1 WHERE user_id=?", (uid,))
                conn.commit()
            finally:
                conn.close()
        add_material(uid, material, mat_amount)
        add_xp(uid, max(10, price // 20))
        check_achievements(uid)

        answer(call, f"🎉 Получен: {artifact[0]}")
        re = RARITIES[artifact[7]]["emoji"]
        text = (
            f"📦 <b>{name}</b>\n\n"
            f"🎉 Выпал артефакт!\n"
            f"{re} <b>{artifact[0]}</b>\n"
            f"{THEMES[artifact[1]]} {artifact[1]} • {artifact[7]}\n"
            f"🆔 ID: <b>#{add_id}</b>\n\n"
            f"🔹 Бонус ресурса: {material} +{mat_amount}"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📦 Ещё кейсы", callback_data="cases"))
        kb.add(types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"))
        kb.add(types.InlineKeyboardButton("⬅️ Главная", callback_data="home"))
        edit_or_send(call, text, kb)
        return

    if data.startswith("item:"):
        item_id = int(data.split(":")[1])
        if not cooldown(uid, "equip", 0.45):
            answer(call, "⏳ Подожди.")
            return

        sanitize_equipment(uid)
        with DB_LOCK:
            conn = db()
            try:
                item = conn.execute(
                    "SELECT * FROM inventory WHERE id=? AND user_id=?",
                    (item_id,uid)
                ).fetchone()
                if not item:
                    answer(call, "Артефакт не найден.")
                    return

                if item["equipped_slot"]:
                    conn.execute(
                        "UPDATE inventory SET equipped_slot='' WHERE id=?",
                        (item_id,)
                    )
                    conn.commit()
                    answer(call, "❌ Артефакт снят.")
                else:
                    art = ART_BY_NAME.get(item["artifact"])
                    if not art:
                        answer(call, "Артефакт повреждён.")
                        return
                    slot = art[2]
                    used = conn.execute(
                        "SELECT id FROM inventory WHERE user_id=? AND equipped_slot=?",
                        (uid,slot)
                    ).fetchone()
                    if used:
                        answer(call, "Этот слот уже занят. Сними предмет из слота.")
                        return
                    count = conn.execute(
                        "SELECT COUNT(*) AS c FROM inventory WHERE user_id=? AND equipped_slot!=''",
                        (uid,)
                    ).fetchone()["c"]
                    if count >= len(SLOTS):
                        answer(call, "Все 6 слотов заняты.")
                        return
                    conn.execute(
                        "UPDATE inventory SET equipped_slot=? WHERE id=? AND user_id=?",
                        (slot,item_id,uid)
                    )
                    conn.commit()
                    answer(call, f"⚔️ Надет: {art[0]}")
            finally:
                conn.close()
        edit_or_send(call, inventory_text(uid), inventory_markup(uid))
        return

    if data == "forge":
        answer(call)
        edit_or_send(call, forge_text(uid), forge_markup(uid))
        return

    if data.startswith("upgrade:"):
        item_id = int(data.split(":")[1])
        if not cooldown(uid, "upgrade", 0.6):
            answer(call, "⏳ Подожди.")
            return
        item = execute(
            "SELECT * FROM inventory WHERE id=? AND user_id=?",
            (item_id,uid), fetchone=True
        )
        if not item:
            answer(call, "Предмет не найден.")
            return
        if item["equipped_slot"]:
            answer(call, "Сначала сними артефакт.")
            return
        if item["level"] >= 50:
            answer(call, "Максимальный уровень.")
            return
        art = ART_BY_NAME[item["artifact"]]
        base_cost = 100 + rarity_index(art[7]) * 150
        cost = int(base_cost * (1.25 ** (item["level"] - 1)))
        u = get_user(uid)
        if u["coins"] < cost:
            answer(call, f"Нужно {fmt(cost)}💰")
            return
        # 85% успех; при неудаче деньги всё равно не пропадают полностью.
        success = random.random() < 0.85
        if success:
            execute(
                "UPDATE inventory SET level=level+1 WHERE id=? AND user_id=?",
                (item_id,uid)
            )
            add_xp(uid, 15)
            answer(call, f"🔨 Успех! Теперь Lv.{item['level']+1}")
        else:
            answer(call, "💨 Улучшение не удалось.")
        add_coins(uid, -cost)
        edit_or_send(call, forge_text(uid), forge_markup(uid))
        return

    if data == "prestige":
        u = get_user(uid)
        if u["level"] < 50:
            answer(call, "Нужен 50 уровень.")
            return
        if not cooldown(uid, "prestige", 2):
            answer(call, "Подожди.")
            return
        with DB_LOCK:
            conn = db()
            try:
                conn.execute("""
                    UPDATE users
                    SET coins=100, energy=100, max_energy=100,
                        base_power=1, base_luck=5, xp=0, level=1,
                        prestige=prestige+1, total_clicks=0, total_cases=0
                    WHERE id=?
                """, (uid,))
                conn.execute("DELETE FROM inventory WHERE user_id=?", (uid,))
                conn.execute("DELETE FROM collection WHERE user_id=?", (uid,))
                conn.execute("DELETE FROM achievements WHERE user_id=?", (uid,))
                conn.commit()
            finally:
                conn.close()
        answer(call, "♻️ Престиж получен!")
        edit_or_send(call, home_text(uid), main_markup())
        return

    if data == "top":
        answer(call)
        edit_or_send(call, top_text(uid), back_markup())
        return

    if data == "bonus":
        if not cooldown(uid, "bonus", 1):
            answer(call, "⏳ Подожди.")
            return
        u = get_user(uid)
        if u["last_daily"] == today():
            answer(call, "Бонус уже получен.")
        else:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            streak = u["daily_streak"] + 1 if u["last_daily"] == yesterday else 1
            reward = 250 + min(streak, 30) * 50
            with DB_LOCK:
                conn = db()
                try:
                    conn.execute(
                        "UPDATE users SET coins=coins+?,daily_streak=?,last_daily=? WHERE id=?",
                        (reward,streak,today(),uid)
                    )
                    conn.commit()
                finally:
                    conn.close()
            add_material(uid, "crystal", 1 if streak % 3 else 3)
            answer(call, f"🎁 +{reward}💰 | серия {streak}")
        edit_or_send(call, bonus_text(uid), back_markup())
        return

    if data == "raid":
        answer(call)
        edit_or_send(call, raid_text(uid), raid_markup())
        return

    if data == "raid_hit":
        if not cooldown(uid, "raid", 0.6):
            answer(call, "⏳ Атака перезаряжается.")
            return
        with DB_LOCK:
            conn = db()
            try:
                raid = conn.execute("SELECT * FROM raid WHERE id=1").fetchone()
                if raid["ends_at"] <= now() or raid["hp"] <= 0:
                    conn.execute(
                        "UPDATE raid SET name=?,max_hp=?,hp=?,ends_at=? WHERE id=1",
                        ("🐲 Древний Титан",800000,800000,now()+86400)
                    )
                    conn.execute("DELETE FROM raid_hits WHERE raid_id=1")
                    conn.commit()
                    raid = conn.execute("SELECT * FROM raid WHERE id=1").fetchone()

                power, luck, crit, _, _ = get_stats(uid)
                user_row = conn.execute("SELECT energy FROM users WHERE id=?", (uid,)).fetchone()
                if not user_row or user_row["energy"] < 3:
                    answer(call, "⚡ Для атаки босса нужно 3 энергии.")
                    return
                conn.execute("UPDATE users SET energy=energy-3 WHERE id=?", (uid,))
                damage = max(1, power * random.randint(2,5))
                if random.randint(1,100) <= min(50, crit):
                    damage *= 2
                damage = min(damage, raid["hp"])
                conn.execute("UPDATE raid SET hp=hp-? WHERE id=1", (damage,))
                conn.execute("""
                    INSERT INTO raid_hits(raid_id,user_id,damage) VALUES(1,?,?)
                    ON CONFLICT(raid_id,user_id) DO UPDATE SET damage=damage+excluded.damage
                """, (uid,damage))
                conn.execute(
                    "UPDATE users SET raid_damage=raid_damage+? WHERE id=?",
                    (damage,uid)
                )
                conn.execute(
                    "UPDATE daily_quests SET raid_damage=raid_damage+? WHERE user_id=?",
                    (damage,uid)
                )
                defeated = (raid["hp"] - damage) <= 0
                conn.commit()
            finally:
                conn.close()
        if defeated:
            reward = 5000 + power * 25
            add_coins(uid, reward)
            add_material(uid, "essence", 10)
            answer(call, f"👹 БОСС ПОВЕРЖЕН! +{fmt(reward)}💰 +10 эссенции")
        add_xp(uid, max(1, damage // 10))
        check_achievements(uid)
        answer(call, f"👹 -{fmt(damage)} HP")
        edit_or_send(call, raid_text(uid), raid_markup())
        return

    if data == "raid_top":
        rows = execute(
            """SELECT u.username,u.first_name,h.damage
               FROM raid_hits h JOIN users u ON u.id=h.user_id
               WHERE h.raid_id=1 ORDER BY h.damage DESC LIMIT 10""",
            fetchall=True
        )
        text = "🏆 <b>ТОП РЕЙДА</b>\n━━━━━━━━━━━━━━━━━━\n"
        for i,r in enumerate(rows,1):
            name = ("@" + r["username"]) if r["username"] else r["first_name"] or str(i)
            text += f"{i}. {name} — {fmt(r['damage'])}\n"
        edit_or_send(call, text, raid_markup())
        return

    if data == "shop":
        answer(call)
        edit_or_send(call, shop_text(uid), shop_markup())
        return

    if data.startswith("buy:"):
        sid = int(data.split(":")[1])
        if not cooldown(uid, "buy", 0.5):
            answer(call, "⏳ Подожди.")
            return
        with DB_LOCK:
            conn = db()
            try:
                item = conn.execute("SELECT * FROM shop WHERE id=?", (sid,)).fetchone()
                u = conn.execute("SELECT coins FROM users WHERE id=?", (uid,)).fetchone()
                if not item or item["stock"] <= 0:
                    answer(call, "Товар закончился.")
                    return
                if u["coins"] < item["price"]:
                    answer(call, "💰 Не хватает монет.")
                    return
                conn.execute("UPDATE users SET coins=coins-? WHERE id=?", (item["price"],uid))
                conn.execute("UPDATE shop SET stock=stock-1 WHERE id=?", (sid,))
                if item["item_type"] == "material":
                    conn.execute(
                        f"UPDATE materials SET {item['item_key']}={item['item_key']}+? WHERE user_id=?",
                        (item["amount"],uid)
                    )
                elif item["item_type"] == "potion":
                    conn.execute("""
                        INSERT INTO potions(user_id,potion,amount) VALUES(?,?,?)
                        ON CONFLICT(user_id,potion) DO UPDATE SET amount=amount+excluded.amount
                    """, (uid,item["item_key"],item["amount"]))
                elif item["item_type"] == "coins":
                    conn.execute(
                        "UPDATE users SET coins=coins+? WHERE id=?",
                        (item["amount"],uid)
                    )
                conn.commit()
            finally:
                conn.close()
        answer(call, "🛒 Покупка совершена.")
        edit_or_send(call, shop_text(uid), shop_markup())
        return

    if data == "potions":
        answer(call)
        edit_or_send(call, potions_text(uid), potions_markup(uid))
        return

    if data.startswith("potion:"):
        key = data.split(":")[1]
        if key not in POTIONS:
            answer(call, "Зелье не найдено.")
            return
        if not cooldown(uid, "potion", 1):
            answer(call, "⏳ Подожди.")
            return
        row = execute(
            "SELECT amount FROM potions WHERE user_id=? AND potion=?",
            (uid,key), fetchone=True
        )
        if not row or row["amount"] <= 0:
            answer(call, "Зелий нет.")
            return
        until = now() + POTIONS[key][4]
        field = POTIONS[key][2]
        bonus = POTIONS[key][3]
        with DB_LOCK:
            conn = db()
            try:
                conn.execute(
                    "UPDATE potions SET amount=amount-1 WHERE user_id=? AND potion=?",
                    (uid,key)
                )
                if key == "luck":
                    conn.execute(
                        "UPDATE effects SET luck_until=?,luck_bonus=? WHERE user_id=?",
                        (until,bonus,uid)
                    )
                elif key == "coins":
                    conn.execute(
                        "UPDATE effects SET coins_until=?,coins_mult=? WHERE user_id=?",
                        (until,200,uid)
                    )
                elif key == "energy":
                    conn.execute(
                        "UPDATE effects SET energy_until=?,energy_bonus=? WHERE user_id=?",
                        (until,bonus,uid)
                    )
                    conn.execute(
                        "UPDATE users SET energy=min(max_energy,energy+?) WHERE id=?",
                        (bonus,uid)
                    )
                elif key == "xp":
                    conn.execute(
                        "UPDATE effects SET xp_until=?,xp_bonus=? WHERE user_id=?",
                        (until,bonus,uid)
                    )
                conn.commit()
            finally:
                conn.close()
        answer(call, f"🧪 Использовано: {POTIONS[key][0]}")
        edit_or_send(call, potions_text(uid), potions_markup(uid))
        return

    if data == "gifts":
        answer(call)
        edit_or_send(call, gifts_text(uid), back_markup())
        return

    answer(call)

# ============================================================
# START
# ============================================================

init_database()

print("=" * 54)
print("ARTIFACT CLICKER v8.2")
print("Бот запускается...")
print("=" * 54)

while True:
    try:
        print("Подключение к Telegram...")
        bot.infinity_polling(
            timeout=20,
            long_polling_timeout=20,
            skip_pending=True,
            allowed_updates=["message", "callback_query"]
        )
    except KeyboardInterrupt:
        print("Бот остановлен.")
        break
    except Exception as e:
        err = str(e)
        print(f"Ошибка соединения: {err}")
        if "409" in err or "Conflict" in err or "terminated by other getUpdates request" in err:
            print("ОШИБКА 409: этот токен уже используется другим запущенным экземпляром бота.")
            print("Останови второй экземпляр или используй новый токен BotFather.")
            break
        print("Повторное подключение через 5 секунд...")
        time.sleep(5)
