import asyncio
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Tokeningizni va guruh ID raqamingizni yozing
TOKEN = "9128227852:AAF2BAuehsWrhbZ57HqTOKHYfmWDH9tcH7Y"
GROUP_ID = -1002020577133

# O'ZINGIZNING TELEGRAM ID RAQAMINGIZNI SHU YERGA YOZING
MY_OWNER_ID = 1097025987

# GURUHDAGI BARCHA A'ZOLARNING USERNAME LARINI SHU YERGA YOZIB CHIQING:
# (Bot hali xabar yozmaganlarni ham darhol chaqirishi uchun)
STATIC_MEMBERS = [
    "@Qobuljon_91",
    "@Davronbek_Olimjonov1",
    "@Муслимахон",
    "@Fayzulloxon",
    "@Shirinaxon",
    "@IQBOLJON JUMABOYEV",
    "@Adhamjonov lhomjon",
    "@Shamshidinova Gulnoza",
    "@BehzodSR",
    "@Yoqubjonova M",
    "@Javlon222MM",
    "@Ulugbek",
    "@Donyorbek",
    "@Xusniddin",
    "@***Mexribonnim***",
    "@Dilyaa_o8",
    "@Gulbahor"
    # Qolgan sinfdoshlarning @username larini vergul bilan shu yerga qo'shing:
    # "@username3",
    # "@username4",
]

# Xotira
last_active = {}  # Oxirgi xabar yozgan vaqti (user_id: datetime)
last_welcomed_date = {}    # Bugun salom berilgan sana (user_id: date)
last_owner_reply_time = None
active_members_list = []  # Guruhda yozgan a'zolar ID ro'yxati
current_user_index = 0


# Foydalanuvchini ko'k rangda belgilanadigan (mention) ko'rinishga keltirish
def get_user_mention_html(user):
    if user.username:
        return f"@{user.username}"
    # Username bo'lmasa ham ismiga bosganda profiliga kiradigan qilib belgilaydi
    safe_name = user.first_name.replace("<", "&lt;").replace(">", "&gt;")
    return f'<a href="tg://user?id={user.id}">{safe_name}</a>'


# Guruhdagi barcha xabarlarni o'qib, ularga qarab javob berish
async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    if not user or user.is_bot:
        return

    now = datetime.now()
    today = now.date()

    # Foydalanuvchini bazaga qo'shamiz
    last_active[user.id] = now
    if user.id not in active_members_list:
        active_members_list.append(user.id)

    # 1-HOLAT: Agar xabar yozgan odam SIZ bo'lsangiz — har 3 soatda 1 marta javob beradi
    if user.id == MY_OWNER_ID:
        global last_owner_reply_time
        if last_owner_reply_time is None or (now - last_owner_reply_time) >= timedelta(hours=3):
            last_owner_reply_time = now
            await update.message.reply_text("Akajonim yozishdan to'xtamang! 🚀")
        return

    # 2-HOLAT: Boshqa a'zolar uchun — bir kunda faqat BIR MARTA javob beradi
    if last_welcomed_date.get(user.id) != today:
        last_welcomed_date[user.id] = today

        sender_mention = get_user_mention_html(user)
        sender_username = f"@{user.username}".lower() if user.username else ""

        # Barcha chaqirilishi kerak bo'lgan odamlar ro'yxatini yig'amiz
        all_mentions = []

        # Avval qo'lda kiritilgan STATIC_MEMBERS ro'yxatidagilarni qo'shamiz
        for username in STATIC_MEMBERS:
            if username.lower() != sender_username:
                all_mentions.append(username)

        # Keyin guruhda xabar yozib ulgurgan (lekin STATIC_MEMBERS da yo'q) a'zolarni qo'shamiz
        for member_id in active_members_list:
            if member_id != user.id:
                try:
                    member_info = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=member_id)
                    m_user = member_info.user
                    if m_user.username:
                        m_tag = f"@{m_user.username}"
                        # Ro'yxatda takrorlanmasligi uchun tekshiramiz
                        if not any(m_tag.lower() == existing.lower() for existing in all_mentions):
                            all_mentions.append(m_tag)
                    else:
                        # Username'i yo'q odamlarni (masalan, ШАХЛО) HTML link orqali chaqiramiz
                        all_mentions.append(get_user_mention_html(m_user))
                except Exception:
                    pass

        if all_mentions:
            others_text = " ".join(all_mentions)
            reply_text = (
                f"Assalomu alaykum {sender_mention}, sizni guruhda ko'rganimdan xursandman, "
                f"hozir qolganlarni chaqiraman! 🤝\n\n"
                f"Qani hamma bu yoqqa: {others_text}"
            )
        else:
            reply_text = (
                f"Assalomu alaykum {sender_mention}, sizni guruhda ko'rganimdan xursandman! 🤝"
            )

        await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)


# Har kuni soat 08:30 da ishlaydigan tekshiruv funksiyasi
async def check_member_activity(context: ContextTypes.DEFAULT_TYPE):
    global current_user_index, active_members_list

    if not active_members_list:
        return

    user_id = active_members_list[current_user_index]

    try:
        chat_member = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        user = chat_member.user
        username_mention = get_user_mention_html(user)

        now = datetime.now()
        last_time = last_active.get(user_id)

        if last_time and (now - last_time) < timedelta(days=1):
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"Raxmat {username_mention}, oqibatingizga ko'z tegmasin, shunday habarlarda bardavom bo'ling, sizdan doimo habar kutamiz! 🌸",
                parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"Diqqat {username_mention}! Bugun guruhda faol bo'lmadingiz, iltimos faollik ko'rsating! ⚠️",
                parse_mode=ParseMode.HTML
            )

        current_user_index = (current_user_index + 1) % len(active_members_list)

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")


# Asosiy ishga tushirish qismi
def main():
    application = Application.builder().token(TOKEN).build()

    # Guruhdagi xabarlarni (matn, rasm, stiker va h.k.) kuzatish
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), track_activity))

    job_queue = application.job_queue

    # Har kuni soat 08:30 da ishlaydi
    job_queue.run_daily(
        check_member_activity,
        time=time(hour=8, minute=30, second=0)
    )

    print("Bot yangilangan ro'yxat bilan ishga tushdi!")
    application.run_polling()


if __name__ == "__main__":
    main()
