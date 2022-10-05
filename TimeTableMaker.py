
admin_chat_id = {}

#from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    #ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
#uuuuuuuuuuuuu
import interface
import core_funcs as cf

def main() -> None:
    """ Configure bot."""
    run_file = "run.ini"
    run_pars = cf.Parser()
    run_pars.load_toml(run_file)

    sucere_pars = cf.Parser()
    sucere_pars.load_toml(run_pars.at('secure_file'))
    #info_pars = cf.Parser()
    #info_pars.load_toml(run_pars.at('info_file'))

    API_TOKEN =  sucere_pars.at('Token')

    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(API_TOKEN).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", bot.user_reg_start)],
        states={
            bot.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.user_reg_age)],
            bot.GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.user_reg_gender)],
            bot.UNIVERSITY: [MessageHandler(filters.Regex("^(Boy|Girl|Other)$"), bot.user_reg_university)],
            bot.FACILITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.user_reg_facility)],
            bot.DISTANCES: [MessageHandler(filters.Regex("^(Горная|Пешеходная|Водная|Вело|Охота на лис)$"), bot.user_reg_distances)],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )

    application.add_handler(conv_handler)
    print("Bot start")

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
  

if __name__ == "__main__":
    main()