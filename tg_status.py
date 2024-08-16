from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
from acc_info import get_positions_str
import time
import asyncio
from close_all import close_positions
import sys

UM = sys.argv[1] == "um"
with open("bot_keys.txt", "r") as f:
    keys = f.readline()[:-1]

ACTIVE = False
async def status(context):
    await context.bot.send_message(context.chat_data["user_id"], 
            text="CURR_POS:\n" + get_positions_str(UM))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(update.effective_chat.id)
    context.chat_data.update({
        "user_id" : update.effective_chat.id,
        "name"    : "STATUS_" + str(update.effective_chat.id)
    })
    context.job_queue.run_repeating(status, 30, 
        chat_id=context.chat_data["user_id"], 
        name=context.chat_data["name"])

def active(context):
    current_jobs = context.job_queue.get_jobs_by_name("STATUS")

    if not current_jobs:
        return False
    return True

async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    close_positions(UM)
    await context.bot.send_message(context.chat_data["user_id"], 
            text="Closing orders submitted")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.chat_data)
    current_jobs = context.job_queue.get_jobs_by_name(context.chat_data["name"])
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text("Upd Stop sent")
    return True


if len(sys.argv) != 2 or sys.argv[1] not in ["cm", "um"]:
    print("Choose cm or um")
    exit(0)


app = Application.builder().token(keys).build()


app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("close_all", close))

app.add_handler(CommandHandler("stop", stop))

app.run_polling()
