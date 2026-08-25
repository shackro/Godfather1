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

# 3. The Memory Map (Tracks Source ID -> Destination ID)
# Note: This resets if the bot restarts. (See note below for persistence)
copied_messages = {}

# 4. Handle NEW Posts
async def copy_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post
    if not message or str(message.chat.id) != str(SOURCE_CHANNEL_ID):
        return

    try:
        # Copy the message and capture the NEW message ID in Channel B
        result = await message.copy(chat_id=DEST_CHANNEL_ID)
        
        # Save the mapping: Source ID -> Destination ID
        copied_messages[message.message_id] = result.message_id
        logger.info(f"✅ Copied message {message.message_id} to {DEST_CHANNEL_ID}")
        
    except Exception as e:
        logger.error(f"❌ Failed to copy message: {e}")

# 5. Handle EDITED Posts (NEW!)
async def edit_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.edited_channel_post
    if not message or str(message.chat.id) != str(SOURCE_CHANNEL_ID):
        return

    source_msg_id = message.message_id
    
    # Check if we actually copied this message earlier
    if source_msg_id in copied_messages:
        dest_msg_id = copied_messages[source_msg_id]
        
        try:
            # If it's a text-only post, edit the text
            if message.text:
                await context.bot.edit_message_text(
                    chat_id=DEST_CHANNEL_ID,
                    message_id=dest_msg_id,
                    text=message.text,
                    entities=message.entities  # Preserves bold/italic/links
                )
            # If it's a photo/document with a caption, edit the caption
            elif message.caption:
                await context.bot.edit_message_caption(
                    chat_id=DEST_CHANNEL_ID,
                    message_id=dest_msg_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities
                )
            else:
                logger.info("⚠️ Edit was media-only (e.g., swapped image). Bots can't edit media directly.")
                
            logger.info(f"🔄 Updated message {source_msg_id} in Channel B")
            
        except Exception as e:
            logger.error(f"❌ Failed to edit message: {e}")
    else:
        logger.warning(f"⚠️ Edited message {source_msg_id} wasn't in our map. (Did the bot restart?)")

# 6. Start the Bot
def main():
    if not BOT_TOKEN:
        raise ValueError("🚨 BOT_TOKEN environment variable is not set!")
    
    logger.info("🚀 Starting Telegram Bot Automation...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Listen for NEW channel posts
    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, copy_channel_post))
    
    # Listen for EDITED channel posts
    application.add_handler(MessageHandler(filters.UpdateType.EDITED_CHANNEL_POST, edit_channel_post))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
