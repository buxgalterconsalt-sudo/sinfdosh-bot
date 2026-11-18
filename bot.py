import asyncio
from datetime import datetime, time, timedelta
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Tokeningizni va aniq guruh ID raqamingizni bu yerga yozing
TOKEN = "9128227852:AAF2BAuehsWrhbZ57HqTOKHYfmWDH9tcH7Y"
GROUP_ID = -1002020577133

# Oxirgi faollik vaqtlarini saqlash uchun lug'at (user_id: datetime)
last_active = {}
# Bugungi navbatdagi foydalanuvchi indeksini saqlash uchun
current_user_index = 0
active_members_list = []  # Guruhda xabar yozgan faol foydalanuvchilar ro'yxati


# 1. Guruhdagi barcha matnli xabarlarni kuzatib, foydalanuvchi faolligini saqlab borish
async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_chat.id == GROUP_ID:
        user = update.effective_user
        if user:
            last_active[user.id] = datetime.now()
            # Agar bu foydalanuvchi ro'yxatda hali bo'lmasa, uni qo'shamiz
            if user.id not in active_members_list:
                active_members_list.append(user.id)


# 2. Test vaqtida ishga tushib, maxsus e'lon yuboradigan funksiya
async def send_startup_announcement(context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Bot ishlab endi sizlarga Qobil akajonimning buyruqlari bilan "
        "har kuni soat 08:30 da salomlashishingizni eslataman. "
        "Qanaqadir shikoyatlar bo'ladigan bo'lsa akamga murojaat qilinglar!"
    )
    await context.bot.send_message(chat_id=GROUP_ID, text=text)


# 3. Har kuni soat 08:30 da ishlaydigan asosiy tekshiruv funksiyasi
async def check_member_activity(context: ContextTypes.DEFAULT_TYPE):
    global current_user_index, active_members_list

    if not active_members_list:
        print("Hali guruhda xabar yozgan foydalanuvchilar ro'yxati bo'sh.")
        return

    # Ro'yxatdan navbatdagi foydalanuvchi ID raqamini olamiz
    user_id = active_members_list[current_user_index]

    try:
        chat_member = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        user = chat_member.user

        username_mention = f"@{user.username}" if user.username else user.first_name

        # Oxirgi 24 soat ichida yozganmi yoki yo'qmi tekshiramiz
        now = datetime.now()
        last_time = last_active.get(user_id)

        if last_time and (now - last_time) < timedelta(days=1):
            # Agar faol bo'lsa
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"Raxmat {username_mention}, oqibatingizga ko'z tegmasin, shunday habarlarda bardavom bo'ling, sizdan doimo habar kutamiz,! 🌸"
            )
        else:
            # Agar faol bo'lmasa
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"Diqqat {username_mention}!  Bugun guruhda faol bo'lmadingiz, iltimos faollik ko'rsating! ⚠️"
            )

        # Keyingi kunga navbatni ro'yxatdagi keyingi odamga o'tkazamiz
        current_user_index = (current_user_index + 1) % len(active_members_list)

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")


# Asosiy ishga tushirish qismi
def main():
    application = Application.builder().token(TOKEN).build()

    # Guruhdagi oddiy xabarlarni kuzatish uchun handler
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_activity))

    job_queue = application.job_queue

    # TEST UCHUN: Bot yoqilgandan 10 sekund o'tib yuqoridagi e'lon matnini yuboradi
    job_queue.run_once(send_startup_announcement, when=10)

    # DOIMIY UCHUN: Har kuni soat 08:30 da a'zolarni navbat bilan tekshirib boradi
    job_queue.run_daily(
        check_member_activity,
        time=time(hour=8, minute=30, second=0)
    )

    print("Bot muvaffaqiyatli ishga tushdi va ishlayapti...")
    application.run_polling()


if __name__ == "__main__":
    main()