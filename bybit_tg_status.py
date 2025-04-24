from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
import time
import asyncio
import sys
from bybit_fut_conn import acc_info, cancel, close as cls, acc_info, HTTP
import configparser as cp

CLI = None
ACTIVE = False

    

async def status(context):
    await context.bot.send_message(context.chat_data["user_id"], 
            text=acc_info(CLI)[2])

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
    cancel(CLI)
    cls(CLI)
    await context.bot.send_message(context.chat_data["user_id"], 
            text="Closing orders submitted")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.chat_data)
    if "name" not in context.chat_data:
        return
    current_jobs = context.job_queue.get_jobs_by_name(context.chat_data["name"])
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text("Upd Stop sent")
    return True


bot_keys = ""
with open(sys.argv[2], "r") as f:
    bot_keys = f.readline()[:-1]


id  = sys.argv[1] 
keys = cp.ConfigParser()
keys.read("FutKeys.ini")
api = keys[f"ACC_{id}"]["api_key"]
sec = keys[f"ACC_{id}"]["secret"]
CLI = HTTP(testnet=False, api_key=api, api_secret=sec)

app = Application.builder().token(bot_keys).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("close_all", close))

app.add_handler(CommandHandler("stop", stop))

app.run_polling()
