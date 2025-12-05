# main.py
import asyncio
import json
import os
import time
import logging
from typing import Dict, List

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ---------------------------
# 1️⃣ CONFIG (HARD-CODED TOKENS)
# ---------------------------
TOKENS: List[str] = [
    "8289738046:AAFTWyR7FySXb4TiEP045omhi1itv9uPg44",
    "8104866154:AAFtzfLoMk9MdBSTn-iZBsmR4q2AAHgo-9E",
    "8139396545:AAFk1cZWNXbHzhAIBnYNY9V3_P4AzoncsSQ",
    "8570238039:AAGB5VdiGWXe3RjrJCoyxhGbFJg_Q3pLbmE",
    "8289123318:AAH7wHsnkdX61BF7XtPGVFkCw4sW6DtTDoY",
    "8414792721:AAEML6F56xHiN3uyWiW3nGlhElB7s7tNtE8",
    "8154439703:AAH0rS3cFx0G57jLEkRWP9sVo6SD-ifClh0"
]

OWNER_ID = 6684078201
SUDO_FILE = "sudo.json"

RAID_TEXTS = [
    "-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ ♥️","-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ 🤍","-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ 🩶",
    "-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ 💙","-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ 🤎","-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ 🖤",
    "-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ 🩵","-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ 💜","-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ ❤️",
    "-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ 💚","-+𝐑𝐀𝐍𝐃𝐀𝐈𝐋+-🪽⚓ 🧡"
]
NCEMO_EMOJIS = RAID_TEXTS.copy()

# ---------------------------
# 2️⃣ SUDO LOAD / SAVE
# ---------------------------
if os.path.exists(SUDO_FILE):
    try:
        with open(SUDO_FILE, "r", encoding="utf-8") as f:
            _loaded = json.load(f)
            SUDO_USERS = set(int(x) for x in _loaded)
    except Exception:
        SUDO_USERS = {OWNER_ID}
else:
    SUDO_USERS = {OWNER_ID}
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump(list(SUDO_USERS), f)


def save_sudo():
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump(list(SUDO_USERS), f)


# ---------------------------
# 3️⃣ GLOBAL STATE
# ---------------------------
group_tasks: Dict[int, Dict[str, asyncio.Task]] = {}
slide_targets = set()
slidespam_targets = set()
swipe_mode = {}
apps: list = []
bots: list = []
delay = 1.0

logging.basicConfig(level=logging.INFO)


# ---------------------------
# 4️⃣ DECORATORS
# ---------------------------
def only_sudo(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id if update.effective_user else None
        if uid not in SUDO_USERS:
            if update.message:
                return await update.message.reply_text("❌ You are not sudo.")
            return
        return await func(update, context)
    return wrapper


def only_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id if update.effective_user else None
        if uid != OWNER_ID:
            if update.message:
                return await update.message.reply_text("❌ You are not the owner.")
            return
        return await func(update, context)
    return wrapper


# ---------------------------
# 5️⃣ BOT LOOP (title changer)
# ---------------------------
async def bot_loop(bot, chat_id: int, base: str, mode: str):
    i = 0
    while True:
        try:
            arr = RAID_TEXTS if mode == "raid" else NCEMO_EMOJIS
            text = f"{base} {arr[i % len(arr)]}"
            await bot.set_chat_title(chat_id, text)
            i += 1
            await asyncio.sleep(delay)
        except Exception as e:
            logging.warning(f"[WARN] Bot error in chat {chat_id}: {e}")
            await asyncio.sleep(2)


# ---------------------------
# 6️⃣ COMMAND HANDLERS
# ---------------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💗 Welcome! Use /help to see commands.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/gcnc <text>\n/ncemo <text>\n/stopgcnc\n/stopall\n/delay <sec>\n/status\n"
        "/targetslide (reply)\n/stopslide (reply)\n/slidespam (reply)\n/stopslidespam (reply)\n"
        "/swipe <name>\n/stopswipe\n/addsudo (reply)\n/delsudo (reply)\n/listsudo\n/myid\n/ping"
    )


async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    latency = int((time.time() - start_time) * 1000)
    await msg.edit_text(f"🏓 Pong! {latency} ms")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Your ID: {update.effective_user.id}")


# GC loops
@only_sudo
async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /gcnc <text>")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for bot in bots:
        key = getattr(bot, "token", str(id(bot)))
        if key not in group_tasks[chat_id]:
            group_tasks[chat_id][key] = asyncio.create_task(bot_loop(bot, chat_id, base, "raid"))
    await update.message.reply_text("🔄 GC loop started.")


@only_sudo
async def ncemo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /ncemo <text>")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for bot in bots:
        key = getattr(bot, "token", str(id(bot)))
        if key not in group_tasks[chat_id]:
            group_tasks[chat_id][key] = asyncio.create_task(bot_loop(bot, chat_id, base, "emoji"))
    await update.message.reply_text("🔄 Emoji loop started.")


@only_sudo
async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in group_tasks:
        for t in group_tasks[chat_id].values():
            t.cancel()
        group_tasks[chat_id] = {}
    await update.message.reply_text("⏹ Loop stopped.")


@only_sudo
async def stopall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(group_tasks.keys()):
        for t in group_tasks[chat_id].values():
            t.cancel()
        group_tasks[chat_id] = {}
    await update.message.reply_text("⏹ All loops stopped.")


@only_sudo
async def delay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global delay
    if not context.args:
        return await update.message.reply_text(f"⏱ Delay: {delay}s")
    try:
        delay = max(0.5, float(context.args[0]))
        await update.message.reply_text(f"✅ Delay set to {delay}s")
    except:
        await update.message.reply_text("⚠️ Invalid number.")


@only_sudo
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 Active Loops:\n"
    for cid, tasks in group_tasks.items():
        msg += f"Chat {cid}: {len(tasks)} bots running\n"
    await update.message.reply_text(msg)


# SUDO management
@only_owner
async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
        SUDO_USERS.add(uid)
        save_sudo()
        await update.message.reply_text(f"✅ {uid} added as sudo.")


@only_owner
async def delsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
        if uid in SUDO_USERS:
            SUDO_USERS.remove(uid)
            save_sudo()
        await update.message.reply_text(f"🗑 {uid} removed.")


@only_sudo
async def listsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 SUDO USERS:\n" + "\n".join(map(str, SUDO_USERS)))


# Slide / swipe
@only_sudo
async def targetslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        slide_targets.add(update.message.reply_to_message.from_user.id)
    await update.message.reply_text("🎯 Target slide added.")


@only_sudo
async def stopslide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        slide_targets.discard(update.message.reply_to_message.from_user.id)
    await update.message.reply_text("🛑 Target slide stopped.")


@only_sudo
async def slidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        slidespam_targets.add(update.message.reply_to_message.from_user.id)
    await update.message.reply_text("💥 Slide spam started.")


@only_sudo
async def stopslidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        slidespam_targets.discard(update.message.reply_to_message.from_user.id)
    await update.message.reply_text("🛑 Slide spam stopped.")


@only_sudo
async def swipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /swipe <name>")
    swipe_mode[update.message.chat_id] = " ".join(context.args)
    await update.message.reply_text(f"⚡ Swipe ON: {swipe_mode[update.message.chat_id]}")


@only_sudo
async def stopswipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    swipe_mode.pop(update.message.chat_id, None)
    await update.message.reply_text("🛑 Swipe stopped.")


# Auto replies
async def auto_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    uid = update.message.from_user.id
    chat_id = update.message.chat_id
    if uid in slide_targets or uid in slidespam_targets or chat_id in swipe_mode:
        for text in RAID_TEXTS:
            await update.message.reply_text(text)


# ---------------------------
# 7️⃣ BUILD & RUN
# ---------------------------
def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("gcnc", gcnc))
    app.add_handler(CommandHandler("ncemo", ncemo))
    app.add_handler(CommandHandler("stopgcnc", stopgcnc))
    app.add_handler(CommandHandler("stopall", stopall))
    app.add_handler(CommandHandler("delay", delay_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(CommandHandler("delsudo", delsudo))
    app.add_handler(CommandHandler("listsudo", listsudo))
    app.add_handler(CommandHandler("targetslide", targetslide))
    app.add_handler(CommandHandler("stopslide", stopslide))
    app.add_handler(CommandHandler("slidespam", slidespam))
    app.add_handler(CommandHandler("stopslidespam", stopslidespam))
    app.add_handler(CommandHandler("swipe", swipe))
    app.add_handler(CommandHandler("stopswipe", stopswipe))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_replies))

    return app


async def run_all_bots():
    global apps, bots
    seen = set()
    unique_tokens = []
    for t in TOKENS:
        if t and t not in seen:
            seen.add(t)
            unique_tokens.append(t)

    for token in unique_tokens:
        try:
            app = build_app(token)
            apps.append(app)
            bots.append(app.bot)
        except Exception as e:
            logging.exception("Failed building app: %s", e)

    # initialize & start all apps
    for app in apps:
        try:
            await app.initialize()
            await app.start()
            # start polling
            await app.updater.start_polling()
            logging.info("Started app for token: %s", getattr(app.bot, "token", "unknown"))
        except Exception as e:
            logging.exception("Failed starting app: %s", e)

    logging.info("🚀 All bots started!")
    await asyncio.Event().wait()


def main():
    try:
        asyncio.run(run_all_bots())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutting down.")


if __name__ == "__main__":
    main()