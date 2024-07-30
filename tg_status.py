from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
from acc_info import get_positions_str
import time
import asyncio


ID = 0
with open("bot_keys.txt", "r") as f:
    keys = f.readline()[:-1]
    ID   = int(f.readline()[:-1])

ACTIVE = False
async def status(context):
    await context.bot.send_message(ID, text=get_positions_str())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not active(context):
        context.job_queue.run_repeating(status, 30, chat_id=ID, name="STATUS")

def active(context):
    current_jobs = context.job_queue.get_jobs_by_name("STATUS")

    if not current_jobs:
        return False
    return True



async def stop(update, context):
    if not active(context):
        return False
    current_jobs = context.job_queue.get_jobs_by_name("STATUS")
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text("Upd Stop sent")
    return True

app = Application.builder().token(keys).build()


app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))

app.run_polling()
