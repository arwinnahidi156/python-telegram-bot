import logging
import sqlite3
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# تنظیمات پایه
TOKEN = "1624432237:sQRpuUGWJu7ajagRPazPrB9wiWwVeAteQEw"
BALE_BASE_URL = "https://tapi.bale.ai/bot"

# مراحل مکالمه
NAME, CAR_TYPE, INSURANCE_TYPE, PHONE = range(4)

# اتصال به دیتابیس (اگر وجود ندارد ساخته می‌شود)
conn = sqlite3.connect('leads.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS leads 
                  (user_id TEXT, name TEXT, car_type TEXT, insurance_type TEXT, phone TEXT)''')
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! خوش آمدید. برای دریافت مشاوره بیمه، لطفاً نام و نام خانوادگی خود را وارد کنید:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("مدل خودروی خود را وارد کنید:")
    return CAR_TYPE

async def get_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['car_type'] = update.message.text
    reply_keyboard = [['شخص ثالث', 'بدنه']]
    await update.message.reply_text("نوع بیمه درخواستی را انتخاب کنید:", 
                                     reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return INSURANCE_TYPE

async def get_insurance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['insurance_type'] = update.message.text
    await update.message.reply_text("در نهایت شماره تماس خود را وارد کنید تا کارشناسان ما با شما تماس بگیرند:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    user_id = update.message.from_user.id
    
    # ذخیره در دیتابیس
    cursor.execute("INSERT INTO leads VALUES (?, ?, ?, ?, ?)", 
                   (user_id, context.user_data['name'], context.user_data['car_type'], 
                    context.user_data['insurance_type'], phone))
    conn.commit()
    
    await update.message.reply_text("اطلاعات شما با موفقیت ثبت شد! کارشناسان ما به زودی با شما تماس خواهند گرفت.", 
                                     reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    # مقداردهی ربات با Base URL بله
    app = Application.builder().token(TOKEN).base_url(BALE_BASE_URL).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CAR_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_car)],
            INSURANCE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_insurance)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
