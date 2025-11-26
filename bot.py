# bot.py
import os
import logging
import uuid
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    InlineQueryHandler,
    CommandHandler,
    filters,
)

# -----------------------------
# BOT TOKEN (from environment)
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

# -----------------------------
# Vertical converter
# -----------------------------
def verticalize(text: str) -> str:
    text = text.upper()
    words = text.split()
    blocks = ["\n".join(list(w)) for w in words]
    return "\n\n".join(blocks)


# -----------------------------
# /start command
# -----------------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = await context.bot.get_me()
    await update.message.reply_text(
        "Hello! I'm alive.\n\n"
        f"Try mentioning me:\n@{me.username} hello world\n\n"
        "Or use inline mode:\nType @YourBotUsername anywhere."
    )


# -----------------------------
# INLINE MODE handler
# -----------------------------
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query or ""

    if not query.strip():
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Type something...",
            input_message_content=InputTextMessageContent("Type text to verticalize."),
        )
        await update.inline_query.answer([result], cache_time=0)
        return

    vertical = verticalize(query)
    result = InlineQueryResultArticle(
        id=str(uuid.uuid4()),
        title="Verticalize text",
        input_message_content=InputTextMessageContent(vertical),
        description="Convert text to vertical uppercase",
    )
    await update.inline_query.answer([result], cache_time=0)


# -----------------------------
# MAIN on_text handler (mentions + replies)
# -----------------------------
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text or ""
    me = await context.bot.get_me()
    bot_username = f"@{me.username}"
    bot_id = me.id

    # 1) Handle replies to the bot
    if update.message.reply_to_message:
        replied = update.message.reply_to_message.from_user
        if replied and replied.id == bot_id:
            cleaned = text.strip()
            if cleaned:
                await update.message.reply_text(verticalize(cleaned))
            return

    # 2) Check mention entities (mention + text_mention)
    has_mention = False
    if update.message.entities:
        for ent in update.message.entities:
            if ent.type == "mention":
                mentioned = text[ent.offset: ent.offset + ent.length]
                if mentioned.lower() == bot_username.lower():
                    has_mention = True
                    break
            elif ent.type == "text_mention" and getattr(ent, "user", None):
                if ent.user.id == bot_id:
                    has_mention = True
                    break

    if not has_mention:
        return

    # Remove the mention and respond
    cleaned = text.replace(bot_username, "").strip()
    if cleaned:
        await update.message.reply_text(verticalize(cleaned))


# -----------------------------
# START BOT
# -----------------------------
def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handler
    app.add_handler(CommandHandler("start", start_cmd))

    # Inline mode
    app.add_handler(InlineQueryHandler(inline_query_handler))

    # ONLY respond when mentioned or replied to
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    app.run_polling()


if __name__ == "__main__":
    main()
