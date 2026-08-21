import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 1. Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. Load Environment Variables
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SOURCE_CHANNEL_ID = os.environ.get("SOURCE_CHANNEL_ID")
DEST_CHANNEL_ID = os.environ.get("DEST_CHANNEL_ID")

# 3. The Automation Logic
async def copy_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post
    
    if not message:
        return

    # Ensure the message is from our specific source channel
    if str(message.chat.id) == str(SOURCE_CHANNEL_ID):
        try:
            # CHANGE IS HERE: Use .copy() instead of .forward()
            await message.copy(chat_id=DEST_CHANNEL_ID)
            logger.info(f"✅ Copied message {message.message_id} to {DEST_CHANNEL_ID} as a new post")
        except Exception as e:
            logger.error(f"❌ Failed to copy message: {e}")

# 4. Start the Bot
def main():
    if not BOT_TOKEN:
        raise ValueError("🚨 BOT_TOKEN environment variable is not set!")
    
    logger.info("🚀 Starting Telegram Bot Automation...")
    
    application = Application.builder().token(BOT_TOKEN).build()

    # Only listen for actual channel posts
    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, copy_channel_post))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()