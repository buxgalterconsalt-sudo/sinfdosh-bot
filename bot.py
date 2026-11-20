import asyncio
from datetime import datetime, time, timedelta, timezone
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Tokeningizni va guruh ID raqamingizni yozing
TOKEN = "9128227852:AAF2BAuehsWrhbZ57HqTOKHYfmWDH9tcH7Y"
GROUP_ID = -1002020577133
MY_OWNER_ID = 1097025987

# Toshkent vaqt mintaqasi (UTC+5) — 08:30 aniq ishlashi uchun
TASHKENT_TZ = timezone(timedelta(hours=5))

# GURUHDAGI BARCHA A'ZOLARNING USERNAME LARINI SHU YERGA YOZING:
STATIC_MEMBERS = [
    "@Gulnoza", "@BehzodSR", "@Yoqubjonova M", "@Davronbek_Olimjonov1", "@Shahlo", "@Shirinaxon", "@Adhamjonov", "@Ulugbek", "@Xusniddin", "@Jumagul", "@Fayzulloxon", "@Javlon222MM", "@Donyorbek", "@Dilyaa_o8", "@Gulbahor"
]

# Xotira
last_active = {}
last_welcomed_date = {}
last_owner_reply_time = None
active_members_list = []
current_duty_index = 0  # Navbatdagi odam raqami

def get_user_mention_html(user):
    if user.username:
        return f"@{user.username}"
    safe_name = user.first_name.replace("<", "&lt;").replace(">", "&gt;")
    return f'<a href="tg://user?id={user.id}">{safe_name}</a>'

# 1. Guruhdagi xabarlarni kuzatish
async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_owner_reply_time
    if not update.effective_chat or update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    if not user or user.is_bot:
        return

    now = datetime.now(TASHKENT_TZ)
    today = now.date()

    last_active[user.id] = now
    if user.id not in active_members_list:
        active_members_list.append(user.id)

    # Agar xabar yozgan odam SIZ bo'lsangiz — har 3 soatda 1 marta javob beradi
    if user.id == MY_OWNER_ID:
        if last_owner_reply_time is None or (now - last_owner_reply_time) >= timedelta(hours=3):
            last_owner_reply_time = now
            await update.message.reply_text("Akajonim yozishdan to'xtamang! 🚀")
        return

    # Boshqa a'zolar uchun — kuniga 1 marta javob berib barchani chaqiradi
    if last_welcomed_date.get(user.id) != today:
        last_welcomed_date[user.id] = today
        sender_mention = get_user_mention_html(user)
        sender_username = f"@{user.username}".lower() if user.username else ""

        all_mentions = [u for u in STATIC_MEMBERS if u.lower() != sender_username]

        for member_id in active_members_list:
            if member_id != user.id:
                try:
                    member_info = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=member_id)
                    m_user = member_info.user
                    if m_user.username:
                        m_tag = f"@{m_user.username}"
                        if not any(m_tag.lower() == existing.lower() for existing in all_mentions):
                            all_mentions.append(m_tag)
                    else:
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
            reply_text = f"Assalomu alaykum {sender_mention}, sizni guruhda ko'rganimdan xursandman! 🤝"

        await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)

# 2. Har kuni soat 08:30 da navbatdagi odamga eslatma yuborish (Asosiy)
async def daily_greeting_duty(context: ContextTypes.DEFAULT_TYPE):
    global current_duty_index

    if not STATIC_MEMBERS:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text="Assalomu alaykum guruh ahli! Barchangizga xayrli tong va barakali kun tilayman! ☀️"
        )
        return

    target_user = STATIC_MEMBERS[current_duty_index]

    message_text = (
        f"Assalomu alaykum guruh ahli! Xayrli tong! ☀️\n\n"
        f"{target_user}, bugun sizning do'stlaringizga salomlashib turish kerakligini "
        f"eslatadigan navbatingiz! Iltimos, barchaga salomlaringizni yo'llang! 🤝🌸"
    )

    try:
        await context.bot.send_message(chat_id=GROUP_ID, text=message_text)
        current_duty_index = (current_duty_index + 1) % len(STATIC_MEMBERS)
    except Exception as e:
        print(f"Xabar yuborishda xatolik: {e}")

# 3. TEST REJIM: Kechikkan 08:30 navbati uchun bir martalik xabar
async def test_delayed_greeting(context: ContextTypes.DEFAULT_TYPE):
    global current_duty_index

    if not STATIC_MEMBERS:
        return

    target_user = STATIC_MEMBERS[current_duty_index]

    test_text = (
        f"Assalomu alaykum guruh ahli! ☀️\n\n"
        f"Bugun soat 08:30 da {target_user} ning salomlashish navbati edi, "
        f"texnik nosozliklar tufayli endi eslatma yuboryapman. "
        f"Marhamat, salomlaringizni yo'llang! 🤝🌸"
    )

    try:
        await context.bot.send_message(chat_id=GROUP_ID, text=test_text)
        # Bugungi navbat o'tgani uchun ertaga keyingi odamga o'tkazib qo'yamiz
        current_duty_index = (current_duty_index + 1) % len(STATIC_MEMBERS)
    except Exception as e:
        print(f"Test xabarida xatolik: {e}")

# Asosiy ishga tushirish qismi
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), track_activity))

    job_queue = application.job_queue

    # TEST UCHUN: Bot ishga tushgandan 10 soniyadan keyin kechikkan navbat xabarini yuboradi
    job_queue.run_once(test_delayed_greeting, when=10)

    # DOIMIY UCHUN: Ertadan boshlab har kuni soat 08:30 da ishlaydi
    job_queue.run_daily(
        daily_greeting_duty,
        time=time(hour=8, minute=30, second=0, tzinfo=TASHKENT_TZ)
    )

    print("Bot ishga tushdi! 10 soniyadan keyin test xabari yuboriladi...")
    application.run_polling()

if __name__ == "__main__":
    main()
