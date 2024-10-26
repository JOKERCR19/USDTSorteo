import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, JobQueue
from datetime import datetime, timedelta

# Variables de entorno para Token y Admin ID
TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Variables globales para el acumulado y participantes
daily_accumulated = 0
weekly_accumulated = 0
participants = []

# Función de inicio y menú principal
def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🎉 ¡Bienvenido a Sorteo USDT Diario! 🎉\n\n"
            "💰 Participa para ganar premios diarios y un acumulado semanal cada domingo 💰\n\n"
            f"💵 Premio Diario Acumulado: {daily_accumulated} USDT\n"
            f"🗓 Premio Semanal Acumulado: {weekly_accumulated} USDT"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Comprar Entradas - 5 USDT", callback_data='buy_ticket')]
        ])
    )

# Función para manejar la compra de entradas
def buy_ticket(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    user = query.from_user
    
    # Verificación de duplicados
    if any(p['id'] == user.id for p in participants):
        query.message.reply_text("Ya estás registrado para el sorteo diario.")
    else:
        participants.append({'id': user.id, 'name': user.first_name})
        global daily_accumulated, weekly_accumulated
        daily_accumulated += 5
        weekly_accumulated += 1.25
        context.bot.send_message(
            chat_id=user.id,
            text=(
                f"✅ ¡Compra exitosa, {user.first_name}! 🎉\n"
                f"Estás participando en el sorteo de hoy a las 20:00.\n\n"
                f"Acumulado Diario: {daily_accumulated} USDT\n"
                f"Acumulado Semanal: {weekly_accumulated} USDT"
            )
        )

# Función para seleccionar y notificar al ganador diario
def draw_daily_winner(context: CallbackContext) -> None:
    global daily_accumulated, weekly_accumulated
    if participants:
        winner = random.choice(participants)
        daily_prize = daily_accumulated * 0.5
        weekly_accumulated += daily_accumulated * 0.25

        # Notificación al ganador y al administrador
        context.bot.send_message(
            chat_id=winner['id'],
            text=f"🎉 ¡Felicidades {winner['name']}! Has ganado {daily_prize} USDT en el sorteo diario. 🎉"
        )
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"Ganador del sorteo diario:\n"
                f"Usuario: @{winner['name']}\n"
                f"Premio: {daily_prize} USDT\n\n"
                f"Premio acumulado semanal actualizado: {weekly_accumulated} USDT"
            )
        )

        daily_accumulated = 0
        participants.clear()
    else:
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text="No hubo participantes en el sorteo diario."
        )

# Función para seleccionar y notificar al ganador semanal
def draw_weekly_winner(context: CallbackContext) -> None:
    global weekly_accumulated
    if participants:
        winner = random.choice(participants)
        context.bot.send_message(
            chat_id=winner['id'],
            text=f"🎉 ¡Felicidades {winner['name']}! Has ganado el acumulado semanal de {weekly_accumulated} USDT. 🎉"
        )
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"Ganador del sorteo semanal:\n"
                f"Usuario: @{winner['name']}\n"
                f"Premio semanal: {weekly_accumulated} USDT"
            )
        )
        weekly_accumulated = 0
    else:
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text="No hubo participantes en el sorteo semanal."
        )

# Función para programar los sorteos automáticos
def schedule_draws(updater: Updater):
    job_queue = updater.job_queue
    job_queue.run_daily(draw_daily_winner, time=datetime.strptime("20:00", "%H:%M").time(), days=(0, 1, 2, 3, 4, 5, 6))
    job_queue.run_daily(draw_weekly_winner, time=datetime.strptime("20:00", "%H:%M").time(), days=(6,))

# Función principal
def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(buy_ticket, pattern='buy_ticket'))
    schedule_draws(updater)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
