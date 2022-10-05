import logging

from datetime import datetime 
from datetime import timedelta 

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
	filename="logs\py_log"+ datetime.today().strftime("-%m.%d.%Y,%H-%M-%S") + ".log",filemode="w"
)
logger = logging.getLogger(__name__)

#user registration steps:
AGE, GENDER, UNIVERSITY, FACILITY, DISTANCES = range(5)

# Handle '/help'
# Дописать!!
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
	text =  """
Привет! Я бот горного Турклуба МГУ. Я совсем маленький, но быстро учусь!
Мои команды:
/start - Регистрация участника на слёт. Во время регистрации можно выбрать интересующие вас _личные_ дистанции.
/new_team - Регистрация команды на командную дистанцию. На каждую дистанцию регистрируется отдельная команда.
/my_dist - Список дистанций (как личных, так и командных, на которые вы зарегистрированы.
/ask_admin - Написанное после этой команды сообщение будет передано администратору. Может пригодится для связи по проблемам или предложениям и замечаниям.
""")
	#bot.register_next_step_handler(msg, process_name_step)

def processing_exceptions(message, Exception):
	bot.reply_to(message, 'Что-то пошло не так( Попробуйте ещё раз!')
	print('Что-то пошло не так( Попробуйте ещё раз!')
	if not admin_chat_id == None:
		bot.send_message(admin_chat_id, e.args)


# Handle '/ask_admin'
MESSAGE_TO_ADMIN = 0
async def process_ask_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text(
	   'Пожалуйста, введите сообщение для Администратора.'
	)
	return MESSAGE_TO_ADMIN

async def process_send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text(
	   'Ваше сообщение передано Администратору.'
	)
	if update.message.chat.has_protected_content or update.message.has_protected_content:
		print("Unavalable")
	# forward_message Не работает

	await update.message.forward(chat_id= cf.admin_chat_id, 
				   #from_chat_id= update.message.chat.id, 
				   disable_notification = True 
				   #message_id= update.message.message_id
				   )
	return ConversationHandler.END

#Handle user_reg
#user registration steps:
AGE, GENDER, UNIVERSITY, FACILITY, DISTANCES = range(5)
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
	if all(x.isalpha() or x.isspace() for x in update.message.text):
		cf.users.user_dict.loc[user.id, 'Name'] = update.message.text
		await update.message.reply_text(
		"Приятно познакомится! "
		"Сколько вам лет?."
		)
		return GENDER
	else:
		await update.message.reply_text(
			"Пожалуйста, напишите имя и фамилию."
			"Для этого вам нужны только буквы и пробелы ;)"
		)
		return AGE
	

async def user_reg_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Stores the selected age and asks for a gender."""
	user = update.message.from_user
	logger.info("Age of %s: %s", user.first_name, update.message.text)

	if update.message.text.isdigit() and  0 < int(update.message.text) and int(update.message.text) < 120:
			cf.users.user_dict.loc[user.id, 'Age'] = update.message.text
			reply_keyboard = [["Мальчик", "Девочка"]]
	
			await update.message.reply_text(
				"Пожалуйста, выберете ваш пол.",
				reply_markup=ReplyKeyboardMarkup(
					reply_keyboard, one_time_keyboard=True, input_field_placeholder="Мальчик или Девочка?"
				),
			)
		
			return UNIVERSITY
	else:
		await update.message.reply_text(
				"Сколько вам лет?"
				"Для этого вам нужны только цифры. Я уверен, что вам где-то от 0 до 120 лет."
			)
		return GENDER

async def user_reg_university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Stores the selected gender and asks for a university."""
	user = update.message.from_user
	logger.info("Univer of %s: %s", user.first_name, update.message.text)

	cf.users.user_dict.loc[user.id, 'Sex'] = update.message.text

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
	
	cf.users.user_dict.loc[user.id, 'University'] = update.message.text
	cf.users.user_dict.loc[user.id, 'Distances'] = []

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

		cf.users.user_dict.loc[user.id, 'Distances'].append(update.message.text)

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
		"Хорошо, поговорим потом!", reply_markup=ReplyKeyboardRemove()
	)

	return ConversationHandler.END
