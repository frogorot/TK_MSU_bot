import logging
import re

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    print(__version_info__)
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import core_funcs as cf


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
    filename="py_log.log",filemode="w"
)
logger = logging.getLogger(__name__)

#user registration steps:
AGE, GENDER, UNIVERSITY, FACILITY, DISTANCES = range(5)

dist_dict = { "Горная" : cf.DistanceResults("Горная"), 
              "Пешеходная" : cf.DistanceResults("Пешеходная"), 
              "Водная" : cf.DistanceResults("Водная"),
              "Вело" : cf.DistanceResults("Вело"),
              "Охота на лис" : cf.DistanceResults("Охота на лис")}
dist_print_pattern = [ [0,2,3],[1,4]]

# Handle '/start' and '/help'
# Дописать!!
#@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    msg = bot.reply_to(message, """\
Привет! Я бот горного Турклуба МГУ. Я совсем маленький, но быстро учусь!
Мои команды:
\start - Регистрация участника на слёт. Во время регистрации можно выбрать интересующие вас _личные_ дистанции.
\new_team - Регистрация команды на командную дистанцию.
\my_dist - Список дистанций, на которые вы зарегистрированы.
\ask_admin - Написанное после этой команды сообщение будет передано администратору. Может пригодится для связи по проблемам или предложениям и замечаниям.
""")
    #bot.register_next_step_handler(msg, process_name_step)

def processing_exceptions(message, Exception):
    bot.reply_to(message, 'Что-то пошло не так( Попробуйте ещё раз!')
    if not admin_chat_id == None:
        bot.send_message(admin_chat_id, e.args)

# Handle '/ask_admin'
#@bot.message_handler(commands=['ask_admin'])
def process_ask_admin(message):
    try:
        msg = bot.reply_to(message, 'Пожалуйста, введите сообщение для Администратора.')
        bot.register_next_step_handler(msg, process_send_to_admin)
    except Exception as e:
        processing_exceptions(message, e)

def process_send_to_admin(message):
    try:
        bot.forwardMessage(chat_id = admin_chat_id, from_chat_id = message.chat.id, message_id = message.message_id)
        msg = bot.reply_to(message, 'Ваше сообщение передано Администратору.')
    except Exception as e:
        processing_exceptions(message, e)


async def user_reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their name."""
    await update.message.reply_text(
       "Ура, давайте знакомится!"
       "Отправьте /cancel чтобы прекратить общение.\n\n"
       "Как вас зовут? Пожалуйста, напишите полные имя и фамилию.",
    )
    return AGE

async def user_reg_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected name and asks for a age."""
    user = update.message.from_user
    logger.info("Name of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "Приятно познакомится! "
        "Сколько вам лет?."
    )

    return GENDER

async def user_reg_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected age and asks for a gender."""
    user = update.message.from_user
    logger.info("Age of %s: %s", user.first_name, update.message.text)

    reply_keyboard = [["Boy", "Girl", "Other"]]
    
    await update.message.reply_text(
        "Пожалуйста, выберете ваш пол.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Мальчик или Девочка?"
        ),
    )
    
    return UNIVERSITY

async def user_reg_university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a university."""
    user = update.message.from_user
    logger.info("Univer of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "В каком вузе вы учитесь? "
        "Если вы не студент, можете написать место работы или поставить \"-\".",
        reply_markup=ReplyKeyboardRemove(),
    )

    return FACILITY

# Надо переделать!!!
async def user_reg_facility(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected university and asks for a facility or for distances."""
    user = update.message.from_user
    logger.info("fasil of %s: %s", user.first_name, update.message.text)
    is_msu = re.search("МГУ", update.message.text)
    if is_msu != None:
        await update.message.reply_text(
            "На каком факультете вы учитесь? "
        )
        return DISTANCES
    else:
        reply_keyboard = [["Горная", "Вело", "Пешеходная"],
                          ["Охота на лис", "Водная"],
                          ["всё"]]
        await update.message.reply_text(
            "На каких дистанциях вы хотели бы участвовать?",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Мальчик или Девочка?"
        ),
        )
        return DISTANCES
    
async def user_reg_distances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    if update.message.text == "всё":
        await update.message.reply_text(
            "Спасибо!",
            reply_markup=ReplyKeyboardRemove(),
            )
        print(logger)
        return ConversationHandler.END
    else:
        logger.info("Dist of %s: %s", user.first_name, update.message.text)

        reply_keyboard = [["Горная", "Вело", "Пешеходная"],
                          ["Охота на лис", "Водная"],
                          ["всё"]]
        await update.message.reply_text(
            "На каких дистанциях вы хотели бы участвовать?",
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Мальчик или Девочка?"
        ),
        )
        return DISTANCES

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END
