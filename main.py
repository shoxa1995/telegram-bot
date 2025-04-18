# main.py
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
)
import os, asyncio

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get('PORT', 5000))
app = Flask(__name__)
telegram_app = ApplicationBuilder().token(TOKEN).build()

user_data = {}
services = {
    "Consultation (30 min)": 100000,
    "IELTS Training (1 hr)": 150000,
    "Visa Assistance": 200000
}

payment_links = {
    "Click Uz": "https://click.uz/your-click-link",
    "Payme": "https://payme.uz/your-payme-link"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in services]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose a service:", reply_markup=reply_markup)

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service = query.data
    user_id = query.from_user.id
    user_data[user_id] = {"service": service, "paid": False}

    buttons = [
        [InlineKeyboardButton("Pay with Click Uz", url=payment_links["Click Uz"])],
        [InlineKeyboardButton("Pay with Payme", url=payment_links["Payme"])]
    ]
    markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(
        text=f"You selected: {service}\n\nPay using the buttons below. After payment, you will be able to pick a time.",
        reply_markup=markup
    )

async def time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = user_data.get(user_id, {})

    if user.get("paid"):
        time = update.message.text
        await update.message.reply_text(
            f"✅ Booking confirmed!\n\nService: {user.get('service')}\nTime: {time}"
        )
    else:
        await update.message.reply_text("Please complete payment first.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(service_selected))
telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), time_handler))

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.run(telegram_app.update_queue.put(update))
    return "ok", 200

@app.route("/payment-confirm", methods=["POST"])
def payment_confirm():
    data = request.json
    user_id = int(data.get("user_id"))
    if user_id in user_data:
        user_data[user_id]["paid"] = True
    return "payment confirmed", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200
