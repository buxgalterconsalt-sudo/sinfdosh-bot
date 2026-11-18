import asyncio
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Tokeningizni va guruh ID raqamingizni yozing
TOKEN = "9128227852:AAF2BAuehsWrhbZ57HqTOKHYfmWDH9tcH7Y"
GROUP_ID = -1002020577133

# O'ZINGIZNING TELEGRAM ID RAQAMINGIZNI SHU YERGA YOZING (masalan: 123456789)
MY_OWNER_ID = 1097025987

# Xotira (Bot qayta yoqilganda avtomatik tozalanadi va bugungi yozganlarga ham qayta javob beradi)
last_active = {}  # Oxirgi xabar yozgan vaqti (user_id: datetime)
last_welcomed_date = {}  # Bugun salom berilgan sana (user_id: date)
active_members_list = []  # Guruhda yozgan barcha a'zolar ro'yxati
current_user_index = 0


# Guruhdagi barcha xabarlarni o'qib, ularga qarab javob berish
async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    if not user or user.is_bot:
        return

    now = datetime.now()
    today = now.date()

    # Foydalanuvchini umumiy ro'yxatga va faollik vaqtiga qo'shamiz
    last_active[user.id] = now
    if user.id not in active_members_list:
        active_members_list.append(user.id)

    # 1-HOLAT: Agar xabar yozgan odam SIZ (Qobil aka) bo'lsangiz — har bir xabaringizga javob beradi
    if user.id == MY_OWNER_ID:
        await update.message.reply_text("Akajonim yozishdan to'xtamang! 🚀")
        return

    # 2-HOLAT: Boshqa a'zolar uchun — bir kunda faqat BIR MARTA javob beradi
    if last_welcomed_date.get(user.id) != today:
        last_welcomed_date[user.id] = today  # Bugungi sanani belgilab qo'yamiz

        username_mention = f"@{user.username}" if user.username else user.first_name

        # Guruhdagi (bazada bor) barcha qolgan a'zolarning @username larini yig'amiz
        other_mentions = []
        for member_id in active_members_list:
            if member_id != user.id:
                try:
                    member_info = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=member_id)
                    m_user = member_info.user
                    m_mention = f"@{m_user.username}" if m_user.username else m_user.first_name
                    other_mentions.append(m_mention)
                except Exception:
                    pass

        if other_mentions:
            others_text = " ".join(other_mentions)
            reply_text = (
                f"Assalomu alaykum {username_mention}, sizni guruhda ko'rganimdan xursandman, "
                f"hozir qolganlarni chaqiraman! 🤝\n\n"
                f"Qani hamma bu yoqqa: {others_text}"
            )
        else:
            reply_text = (
                f"Assalomu alaykum {username_mention}, sizni guruhda ko'rganimdan xursandman! 🤝\n"
                f"(Hozircha ro'yxatda boshqa a'zolar yo'q, ular ham yozishsa saqlab olaman)"
            )

        await update.message.reply_text(reply_text)


# Har kuni soat 08:30 da ishlaydigan tekshiruv funksiyasi
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

    # Guruhdagi oddiy xabarlarni ushlab qolish
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_activity))

    job_queue = application.job_queue

    # Har kuni soat 08:30 da ishlaydi
    job_queue.run_daily(
        check_member_activity,
        time=time(hour=8, minute=30, second=0)
    )

    print("Bot qayta ishga tushdi! Xotira tozalandi, test qilishga tayyor...")
    application.run_polling()


if __name__ == "__main__":
    main()