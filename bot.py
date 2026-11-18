import asyncio
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Tokeningizni va aniq guruh ID raqamingizni bu yerga yozing
TOKEN = "9128227852:AAF2BAuehsWrhbZ57HqTOKHYfmWDH9tcH7Y"
GROUP_ID = -1002020577133

# Oxirgi faollik vaqtlarini saqlash uchun lug'at (user_id: datetime)
last_active = {}
current_user_index = 0
active_members_list = []  # Guruhda xabar yozgan faol foydalanuvchilar ro'yxati


# 1. Guruhda kimdir yozsa, javob berish va faollikni saqlash
async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_chat.id == GROUP_ID:
        user = update.effective_user
        if user:
            # Agar bu foydalanuvchi birinchi marta yozayotgan bo'lsa, javob qaytaramiz
            if user.id not in last_active:
                username_mention = f"@{user.username}" if user.username else user.first_name
                reply_text = (
                    f"Assalomu alaykum {username_mention}, sizni guruhda ko'rganimdan xursandman, "
                    f"hozir qolganlarni chaqiraman! 🤝\n"
                    f"(ID: {user.id})"
                )
                await update.message.reply_text(reply_text)

            # Vaqtni yangilaymiz va ro'yxatga qo'shamiz
            last_active[user.id] = datetime.now()
            if user.id not in active_members_list:
                active_members_list.append(user.id)


# 2. Har kuni soat 08:30 da ishlaydigan tekshiruv funksiyasi
async def check_member_activity(context: ContextTypes.DEFAULT_TYPE):
    global current_user_index, active_members_list

    if not active_members_list:
        return

    user_id = active_members_list[current_user_index]

    try:
        chat_member = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        user = chat_member.user
        username_mention = f"@{user.username}" if user.username else user.first_name

        now = datetime.now()
        last_time = last_active.get(user_id)

        if last_time and (now - last_time) < timedelta(days=1):
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"Raxmat {username_mention}, oqibatingizga ko'z tegmasin, shunday habarlarda bardavom bo'ling, sizdan doimo habar kutamiz! 🌸"
            )
        else:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"Diqqat {username_mention}! Bugun guruhda faol bo'lmadingiz, iltimos faollik ko'rsating! ⚠️"
            )

        current_user_index = (current_user_index + 1) % len(active_members_list)

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")


# Asosiy ishga tushirish qismi
def main():
    application = Application.builder().token(TOKEN).build()

    # Guruhdagi oddiy xabarlarni ushlab qolish uchun handler
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_activity))

    job_queue = application.job_queue

    # Har kuni soat 08:30 da ishlaydi
    job_queue.run_daily(
        check_member_activity,
        time=time(hour=8, minute=30, second=0)
    )

    print("Bot muvaffaqiyatli ishga tushdi va ishlayapti...")
    application.run_polling()


if __name__ == "__main__":
    main()