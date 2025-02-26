from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
from acc_info import get_positions_str, set_client, clientUM
import time
import asyncio
from close_all import close_positions
import sys
from fut_conn import download_trades

UM = sys.argv[1] == "um"
with open(sys.argv[2], "r") as f:
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
    if "name" not in context.chat_data:
        return
    current_jobs = context.job_queue.get_jobs_by_name(context.chat_data["name"])
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text("Upd Stop sent")
    return True

async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    download_trades(clientUM)
    await context.bot.send_document(context.chat_data["user_id"],
                                    open("tmp.csv", "r"))

if len(sys.argv) != 4 or sys.argv[1] not in ["cm", "um"]:
    print("Choose cm or um and provide file with bot keys")
    exit(0)

set_client(int(sys.argv[3]))

app = Application.builder().token(keys).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("close_all", close))

app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("orders", orders))

app.run_polling()
