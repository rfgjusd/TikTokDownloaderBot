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
BOT_TOKEN = os.getenv("BOT_TOKEN")

TIKTOK_PATTERN = re.compile(
    r"https?://(www\.|vm\.|vt\.)?tiktok\.com/\S+"
)


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
        "Привет, этого бота создал Timulik! 👋 Отправь мне ссылку на TikTok-видео, и я попробую скачать его."
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
