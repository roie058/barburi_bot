import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Define the password
AUTHORIZED_USERS_FILE = "data/authorized_users.txt"
PASSWORD = "1234"
AUTHORIZED_USERS = set()


# פונקציה לטעינת משתמשים מורשים מהקובץ
def load_authorized_users():
    if os.path.exists(AUTHORIZED_USERS_FILE):
        with open(AUTHORIZED_USERS_FILE, "r") as file:
            for line in file:
                AUTHORIZED_USERS.add(int(line.strip()))  # שמירת ה-Chat ID כמספר


# פונקציה לשמירת משתמשים מורשים לקובץ
def save_authorized_user(user_id):
    with open(AUTHORIZED_USERS_FILE, "a") as file:
        file.write(f"{user_id}\n")


# טעינת משתמשים מורשים עם הפעלת הבוט
load_authorized_users()


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("You are already logged in!")
        return
    await update.message.reply_text("Welcome! Please enter the password to access the bot:")


async def password(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if len(context.args) == 0:
        await update.message.reply_text("Please enter a password after the command.")
        return

    entered_password = context.args[0]
    if entered_password == PASSWORD:
        AUTHORIZED_USERS.add(user_id)
        save_authorized_user(user_id)  # שמירה לקובץ
        await update.message.reply_text("Correct password! You now have access to the bot.")
    else:
        await update.message.reply_text("Incorrect password. Please try again.")


async def broadcast(update: Update, context: CallbackContext) -> None:
    """
    This function sends the provided message to all users that have successfully authenticated.
    To use: /broadcast your message here
    """
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a message to broadcast.")
        return

    message_to_send = " ".join(context.args)
    for user_id in AUTHORIZED_USERS:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_to_send)
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")
    await update.message.reply_text("Broadcast message sent to authorized users.")


# Create a new application with your bot token
TOKEN = "7599624940:AAF93dleDtTSNCpZxkcgvJh4ZA-l1WbzU2w"
app = Application.builder().token(TOKEN).build()

# Add command handlers to the bot
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("password", password))
app.add_handler(CommandHandler("broadcast", broadcast))

# Start the bot
print("Bot is running...")
app.run_polling()
