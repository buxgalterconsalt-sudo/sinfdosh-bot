import asyncio
from datetime import datetime, time, timedelta
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Tokeningizni va guruh ID raqamingizni bu yerga yozing
TOKEN = "9128227852:AAF2BAuehsWrhbZ57HqTOKHYfmWDH9tcH7Y"
GROUP_CHAT_ID = -1002020577133

# Oxirgi faollik vaqtlarini saqlash uchun lug'at (user_id: datetime)
last_active = {}
# Bugungi navbatdagi foydalanuvchi indeksini saqlash uchun
current_user_index = 0
active_members_list = []  # Guruhdagi faol foydalanuvchilar ro'yxati


# 1. Guruhdagi xabarlarni kuzatib, foydalanuvchi faolligini saqlab borish
async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_chat.id == GROUP_ID:
        user = update.effective_user
        if user:
            last_active[user.id] = datetime.now()
            # Agar bu foydalanuvchi ro'yxatda bo'lmasa, qo'shib qo'yamiz
            if user.id not in active_members_list:
                active_members_list.append(user.id)


# 2. Tekshiruv funksiyasi (Hozir test uchun va har kuni 08:30 da ishlaydi)
async def check_member_activity(context: ContextTypes.DEFAULT_TYPE):
    global current_user_index, active_members_list

    if not active_members_list:
        return  # Hali guruhda xabar yozganlar bo'lmasa kutib turadi

    # Navbatdagi foydalanuvchini tanlaymiz
    user_id = active_members_list[current_user_index]

    try:
        # Foydalanuvchi ma'lumotlarini (username) Telegram'dan olamiz
        chat_member = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        user = chat_member.user

        username_mention = f"@{user.username}" if user.username else user.first_name

        # Oxirgi 24 soat ichida yozganmi yoki yo'qmi tekshiramiz
        now = datetime.now()
        last_time = last_active.get(user_id)

        if last_time and (now - last_time) < timedelta(days=1):
            # Agar yozgan bo'lsa
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"Raxmat {username_mention}, oqibatingizga ko'z tegmasin, shunday habarlarda bardavom bo'ling, sizdan doimo habar kutamiz! 🌸"
            )
        else:
            # Agar yozmagan bo'lsa
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"Diqqat {username_mention}! Eslatma: bugungi navbat sizniki, iltimos faollik ko'rsating! ⚠️"
            )

        # Keyingi kunga navbatdagi odamga o'tamiz
        current_user_index = (current_user_index + 1) % len(active_members_list)

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")


# Asosiy ishga tushirish qismi
def main():
    application = Application.builder().token(TOKEN).build()

    # Xabarlarni kuzatish uchun handler
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_activity))

    job_queue = application.job_queue

    # 1. TEST UCHUN: Bot ishga tushishi bilan 10 sekunddan keyin bir marta ishlaydi
    job_queue.run_once(check_member_activity, when=10)

    # 2. DOIMIY UCHUN: Keyingi kunlardan boshlab har kuni soat 08:30 da ishlaydi
    job_queue.run_daily(
        check_member_activity,
        time=time(hour=8, minute=30, second=0)
    )

    # Botni ishga tushirish
    application.run_polling()


if __name__ == "__main__":
    main()