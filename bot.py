import telebot
import gspread
import ssl
from oauth2client.service_account import ServiceAccountCredentials

# Перевірка SSL
try:
    ssl.create_default_context()
except AttributeError:
    raise ImportError("SSL модуль відсутній або некоректно налаштований. Переконайтеся, що він встановлений у вашій системі.")

# Telegram-бот
TOKEN = "7588961908:AAFjm3jHM5vdlFQGDKYKxEXuPLwO8RdVDuM"
bot = telebot.TeleBot(TOKEN)

# Google Sheets
SHEET_ID = "19cFGOkNgm0hcmy3vD0fRjPxdJb7kOsl0iX19jolTf6I"
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "ecolandbot-8009fea304c0.json"

creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# 🔹 Категорії
EXPENSE_CATEGORIES = ["Добрива", "ЗЗР", "Робота", "Інше"]
CATEGORY_COLUMNS = {"Добрива": "A", "ЗЗР": "E", "Робота": "I", "Інше": "M"}
CULTURES = ["Полуниця", "Малина", "Броколлі", "Пекінська", "Білокачанна"]

# 🔹 Користувацькі дані
user_data = {}

# 🔹 **Обробка команди /start**
@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {"type": None}  # Очищення перед новим вибором
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Витрати", "Доходи", "Статистика")
    bot.send_message(message.chat.id, "Оберіть розділ:", reply_markup=markup)

# 🔹 **Обробка вибору "Витрати"**
@bot.message_handler(func=lambda message: message.text == "Витрати")
def show_expenses(message):
    user_data[message.chat.id] = {"type": "expense"}  # Оновлення типу операції
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*EXPENSE_CATEGORIES)
    bot.send_message(message.chat.id, "Оберіть категорію витрат:\n/start", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["type"] == "expense" and "category" not in user_data[message.chat.id])
def get_expense_category(message):
    if message.text not in EXPENSE_CATEGORIES:
        bot.send_message(message.chat.id, "❌ Невірна категорія. Оберіть зі списку.")
        return
    user_data[message.chat.id]["category"] = message.text
    bot.send_message(message.chat.id, "Введіть назву витрати:\n/start")

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["type"] == "expense" and "name" not in user_data[message.chat.id])
def get_expense_name(message):
    user_data[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "Додайте примітку (дата, пояснення тощо):\n/start")

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["type"] == "expense" and "note" not in user_data[message.chat.id])
def get_expense_note(message):
    user_data[message.chat.id]["note"] = message.text
    bot.send_message(message.chat.id, "Введіть суму (грн):")

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["type"] == "expense" and "amount" not in user_data[message.chat.id])
def get_expense_amount(message):
    try:
        user_data[message.chat.id]["amount"] = float(message.text)
        save_expense(message)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введіть числове значення для суми.")

# 🔹 **Функція запису витрат у Google Sheets**
def save_expense(message):
    try:
        category = user_data[message.chat.id].get("category")
        column = CATEGORY_COLUMNS.get(category)
        last_row = len(sheet.col_values(ord(column) - 64)) + 1
        sheet.update(f"{column}{last_row}", [[user_data[message.chat.id]["name"]]])
        sheet.update(f"{chr(ord(column) + 1)}{last_row}", [[user_data[message.chat.id]["note"]]])
        sheet.update(f"{chr(ord(column) + 2)}{last_row}", [[user_data[message.chat.id]["amount"]]])
        bot.send_message(message.chat.id, "✅ Дані успішно записані! Продовжити /start")
        del user_data[message.chat.id]
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка запису даних: {str(e)}")

# 🔹 **Обробка вибору "Доходи"**
@bot.message_handler(func=lambda message: message.text == "Доходи")
def show_income(message):
    user_data[message.chat.id] = {"type": "income"}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*CULTURES)
    bot.send_message(message.chat.id, "Оберіть культуру:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["type"] == "income" and "culture" not in user_data[message.chat.id])
def get_culture(message):
    user_data[message.chat.id]["culture"] = message.text
    bot.send_message(message.chat.id, "Введіть дату (формат: ДД/ММ):")

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["type"] == "income" and "date" not in user_data[message.chat.id])
def get_income_date(message):
    user_data[message.chat.id]["date"] = message.text
    bot.send_message(message.chat.id, "Введіть вагу (кг):")

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["type"] == "income" and "weight" not in user_data[message.chat.id])
def get_income_weight(message):
    try:
        user_data[message.chat.id]["weight"] = float(message.text)
        bot.send_message(message.chat.id, "Введіть ціну (грн/кг):")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введіть числове значення для ваги.")

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["type"] == "income" and "price" not in user_data[message.chat.id])
def get_income_price(message):
    try:
        user_data[message.chat.id]["price"] = float(message.text)
        save_income(message)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введіть числове значення для ціни.")

def save_income(message):
    try:
        last_row = len(sheet.col_values(19)) + 1  # Колонка S (19 у ASCII)
        sheet.update(f"S{last_row}", [[user_data[message.chat.id]["culture"]]])
        sheet.update(f"T{last_row}", [[user_data[message.chat.id]["date"]]])
        sheet.update(f"U{last_row}", [[user_data[message.chat.id]["weight"]]])
        sheet.update(f"V{last_row}", [[user_data[message.chat.id]["price"]]])

        total_income = user_data[message.chat.id]["weight"] * user_data[message.chat.id]["price"]
        bot.send_message(message.chat.id, f"✅ Дані успішно записані! {total_income} грн. Продовжити /start")

        del user_data[message.chat.id]  # Очистка після запису
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка запису даних: {str(e)}")

# 🔹 Категорія "Статистика"
from telebot.types import ReplyKeyboardRemove

# 🔹 Категорія "Статистика"
@bot.message_handler(func=lambda message: message.text == "Статистика")
def get_statistics(message):
    try:
        # Приховуємо кнопки після вибору
        bot.send_message(message.chat.id, "⏳ Отримую статистику...", reply_markup=ReplyKeyboardRemove())

        # Загальні фінансові показники
        expenses = sheet.acell("R1").value or "0"
        revenue = sheet.acell("R2").value or "0"
        net_profit = sheet.acell("R3").value or "0"

        # Витрати за категоріями
        fert_expense = sheet.acell("C1").value or "0"
        ppp_expense = sheet.acell("G1").value or "0"
        work_expense = sheet.acell("K1").value or "0"
        other_expense = sheet.acell("O1").value or "0"

        # Дані по культурам
        strawberry_weight = sheet.acell("R7").value or "0"
        strawberry_revenue = sheet.acell("R8").value or "0"

        raspberry_weight = sheet.acell("R16").value or "0"
        raspberry_revenue = sheet.acell("R17").value or "0"

        pekinese_weight = sheet.acell("R20").value or "0"
        pekinese_revenue = sheet.acell("R21").value or "0"

        broccoli_weight = sheet.acell("R24").value or "0"
        broccoli_revenue = sheet.acell("R25").value or "0"

        cabbage_weight = sheet.acell("R28").value or "0"
        cabbage_revenue = sheet.acell("R29").value or "0"

        # Формуємо повідомлення статистики
        stats_message = (
            "📊 *Статистика:*\n"
            f"💰 Витрати: *{expenses}* грн\n"
            f"📈 Виручка: *{revenue}* грн\n"
            f"💵 Чистий прибуток: *{net_profit}* грн\n\n"
            "🛠 *Витрати за категоріями:*\n"
            f"🌱 Добрива: *{fert_expense}* грн\n"
            f"🛡 ЗЗР: *{ppp_expense}* грн\n"
            f"👷 Робота: *{work_expense}* грн\n"
            f"📦 Інше: *{other_expense}* грн\n\n"
            "🌿 *Дані по культурам:*\n"
            f"🍓 Полуниця: {strawberry_weight} кг | {strawberry_revenue} грн\n"
            f"🍇 Малина: {raspberry_weight} кг | {raspberry_revenue} грн\n"
            f"🥬 Пекінська капуста: {pekinese_weight} кг | {pekinese_revenue} грн\n"
            f"🥦 Броколі: {broccoli_weight} кг | {broccoli_revenue} грн\n"
            f"🥬 Білокачанна капуста: {cabbage_weight} кг | {cabbage_revenue} грн\n\n"
            "🔄 /start"
        )

        bot.send_message(message.chat.id, stats_message, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка отримання статистики: {str(e)}", reply_markup=ReplyKeyboardRemove())

bot.polling(none_stop=True)
