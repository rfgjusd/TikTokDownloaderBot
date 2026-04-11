import os
import re
import tempfile
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# НАСТРОЙКИ
# =========================

import os
import re
import tempfile
import json
from yt_dlp import YoutubeDL
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# НАСТРОЙКИ
# =========================
BOT_TOKEN = "BOT_TOKEN"

TIKTOK_PATTERN = re.compile(r"https?://.*tiktok\.com/\S+")

STATS_FILE = "stats.json"

# =========================
# STATS FUNCTIONS
# =========================

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def increment_user(user_id: int, username: str):
    data = load_stats()

    uid = str(user_id)
    if uid not in data:
        data[uid] = {"count": 0, "username": username}

    data[uid]["count"] += 1
    data[uid]["username"] = username

    save_stats(data)


def get_user_stats(user_id: int):
    data = load_stats()
    return data.get(str(user_id), {"count": 0, "username": "unknown"})


# =========================
# DOWNLOAD FUNCTION
# =========================

def download_tiktok_video(url: str) -> str:
    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/best",
        "quiet": True,
        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if os.path.exists(filename):
        return filename

    for file in os.listdir(temp_dir):
        return os.path.join(temp_dir, file)

    raise FileNotFoundError("Video not found")


# =========================
# UI
# =========================

menu_keyboard = ReplyKeyboardMarkup(
    [["📥 Скачать видео", "👤 Профиль"]],
    resize_keyboard=True
)


# =========================
# HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋\nОтправь ссылку TikTok или используй меню ниже.",
        reply_markup=menu_keyboard
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user

    # PROFILE
    if text == "👤 Профиль":
        stats = get_user_stats(user.id)
        await update.message.reply_text(
            f"👤 Профиль:\n"
            f"Ник: @{stats['username']}\n"
            f"Скачано видео: {stats['count']}"
        )
        return

    # MENU
    if text == "📥 Скачать видео":
        await update.message.reply_text("Просто отправь ссылку на TikTok-видео 👍")
        return

    # CHECK LINK
    if not TIKTOK_PATTERN.search(text):
        await update.message.reply_text("Отправь корректную ссылку TikTok 👇")
        return

    await update.message.reply_text("⏬ Скачиваю видео...")

    try:
        video_path = download_tiktok_video(text)

        with open(video_path, "rb") as video:
            await update.message.reply_video(video=video)

        increment_user(user.id, user.username or "unknown")

        os.remove(video_path)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


# =========================
# MAIN
# =========================

def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

TIKTOK_PATTERN = re.compile(r"https?://(www\.)?(vm\.)?tiktok\.com/\S+")


def download_tiktok_video(url: str) -> str:
    """Скачивает видео TikTok и возвращает путь к mp4 файлу."""
    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/best",
        "quiet": True,
        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    # Если yt-dlp сохранил не mp4, пробуем найти файл
    if os.path.exists(filename):
        return filename

    for file in os.listdir(temp_dir):
        full = os.path.join(temp_dir, file)
        if os.path.isfile(full):
            return full

    raise FileNotFoundError("Видео не удалось найти после скачивания")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет, этот бот создал Timulik! 👋 Отправь мне ссылку на TikTok-видео, и я попробую скачать его."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not TIKTOK_PATTERN.search(text):
        await update.message.reply_text("Пожалуйста, отправь корректную ссылку TikTok.")
        return

    await update.message.reply_text("⏬ Скачиваю видео, подожди...")

    try:
        video_path = download_tiktok_video(text)

        with open(video_path, "rb") as video:
            await update.message.reply_video(video=video)

        os.remove(video_path)

    except Exception as e:
        await update.message.reply_text(f"Ошибка при скачивании: {e}")


def main():
    # Увеличенные таймауты + более стабильная работа в медленных сетях/VPN
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
