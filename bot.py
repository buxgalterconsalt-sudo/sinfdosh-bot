import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Loglarni sozlash
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = "9128227852:AAF2BAuehsWrhbZ57HqTOKHYfmWDH9tcH7Y"
GROUP_CHAT_ID = -1002020577133


# 1. MA'LUMOTLAR BAZASINI SOZLASH
def init_db():
    conn = sqlite3.connect("sinfdoshlar.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            last_greet_date TEXT
        )
    """)
    conn.commit()
    conn.close()


# Foydalanuvchi xabar yozganda uni bazaga qo'shish yoki sanasini yangilash
def update_member_activity(user_id: int, full_name: str):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("sinfdoshlar.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO members (user_id, full_name, last_greet_date)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            full_name = excluded.full_name,
            last_greet_date = excluded.last_greet_date
    """, (user_id, full_name, today))
    conn.commit()
    conn.close()


# 2. GURUHDAGI XABARLARNI KUZATISH VA HAR BIR YOZGAN ODAMNI SAQLASH
async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id != GROUP_CHAT_ID:
        return

    user = update.effective_user
    if not user or user.is_bot:
        return

    update_member_activity(user.id, user.first_name)
    logging.info(f"✅ {user.first_name} ({user.id}) faol bo'ldi va bazaga yozildi.")


# 3. BUGUN YOZMAGANLARNI TEKshirib, ESLATMA YUBORISH
async def remind_silent_classmates(context: ContextTypes.DEFAULT_TYPE):
    current_hour = datetime.now().hour
    if current_hour >= 23 or current_hour < 8:
        return

    today = datetime.now().strftime("%Y-%m-%d")

    # Guruhdagi barcha a'zolarni Telegram chatidan olishga harakat qilamiz
    try:
        # Telegram chatidagi administratorlar yoki a'zolarni to'liq olish imkoniyati cheklangan bo'lsa,
        # bazadagi ma'lumotlarga tayanamiz. Lekin bazaga avval yozgan barcha sinfdoshlar tushadi.
        conn = sqlite3.connect("sinfdoshlar.db")
        cursor = conn.cursor()

        # Bugun sana yozilmagan yoki bugungi sanaga mos kelmaydiganlar
        cursor.execute("""
            SELECT user_id, full_name FROM members
            WHERE last_greet_date != ? OR last_greet_date IS NULL
        """, (today,))
        silent_users = cursor.fetchall()
        conn.close()

        if not silent_users:
            logging.info("Bugun hamma sinfdoshlar salomlashib bo'lgan!")
            return

        mentions = []
        for user_id, full_name in silent_users:
            safe_name = full_name.replace("<", "").replace(">", "")
            mentions.append(f'<a href="tg://user?id={user_id}">{safe_name}</a>')

        names_list = ", ".join(mentions)
        message_text = (
            f"👋 Hurmatli sinfdoshlar: {names_list}!\n\n"
            f"Bugun guruhda hali ko'rinish bermadingiz va salomlashmadingiz. "
            f"Ahvollaringiz yaxshimi? Bir salom berib qo'yinglar! 😊"
        )

        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message_text,
            parse_mode=ParseMode.HTML
        )
        logging.info("📢 Faol bo'lmagan sinfdoshlarga eslatma yuborildi!")

    except Exception as e:
        logging.error(f"Eslatma yuborishda xatolik: {e}")


# 4. ASOSIY ISHGA TUSHIRISH QISMI
def main():
    init_db()

    application = ApplicationBuilder().token(TOKEN).build()

    # Guruhdagi barcha xabarlarni kuzatish
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_messages))

    # Test uchun hozircha har 1 daqiqada tekshiradigan qilib turamiz (keyin 3 soatga o'zgartirasiz)
    application.job_queue.run_repeating(remind_silent_classmates, interval=60, first=10)

    print("🚀 Sinfdoshlar nazoratchi boti ishga tushdi...")
    application.run_polling()


if __name__ == "__main__":
    main()