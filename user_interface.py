import logging
import time

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
AGE, GENDER, UNIVERSITY, FACILITY, DISTANCES, EXIT = range(6)

###########################################
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


def processing_exceptions(message, context: ContextTypes.DEFAULT_TYPE,  excep: Exception):

	print('Что-то пошло не так( Попробуйте ещё раз!')
	if not admin_chat_id == None:
		message.forward(chat_id= cf.admin_chat_id, 
				   #from_chat_id= update.message.chat.id, 
				   disable_notification = True 
				   #message_id= update.message.message_id
				   )
		context.bot.send_message(chat_id= cf.admin_chat_id,
						   text = excep.args)

###########################################
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

###########################################
#Handle user_reg
#user registration steps:
AGE, GENDER, UNIVERSITY, FACILITY, DISTANCES = range(5)

async def user_reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Starts the conversation and asks the user about their name."""

	user_id = update.message.from_user.id
	for col in cf.users.user_dict.columns:
		cf.users.user_dict.loc[user_id, col] = None
	cf.users.user_dict.loc[user_id, 'Tg_id'] = user_id
	cf.users.user_dict.loc[user_id, cf.users.RES_TIME] = []

	await update.message.reply_text(
	   "Ура, давайте знакомится!\n"
	   "Ваш id: " + str(update.message.from_user.id) + ". Он может понадобится для общения со мной.\n"
	   "Отправьте /cancel чтобы прекратить общение.\n\n"
	   "Как вас зовут? Пожалуйста, напишите полные имя и фамилию.",
	)
	return AGE

async def user_reg_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Stores the selected name and asks for a age."""
	user = update.message.from_user
	logger.info("Name of %s, %s: %s", user.first_name, user.id, update.message.text)
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
		return None # При возврате None  остаётся текущее состояние.
	

async def user_reg_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Stores the selected age and asks for a gender."""
	user = update.message.from_user
	logger.info("Age of %s, %s: %s", user.first_name, user.id,update.message.text)

	age = update.message.text
	if age.isdigit() and  0 < int(age) and int(age) < 120:
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
		return None

async def user_reg_university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Stores the selected gender and asks for a university."""
	user = update.message.from_user
	logger.info("Sex of %s, %s: %s", user.first_name, user.id,update.message.text)

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
	logger.info("Univer of %s, %s: %s", user.first_name, user.id,update.message.text)
	
	cf.users.user_dict.loc[user.id, 'University'] = update.message.text

	is_msu = re.search("МГУ", update.message.text)
	if is_msu != None:
		await update.message.reply_text(
			"На каком факультете вы учитесь? "
		)
		#return DISTANCES
	else:
		await update.message.reply_text(
			"На каких дистанциях вы хотели бы участвовать?",
			reply_markup=ReplyKeyboardMarkup(
			cf.dist_personal_keyboard, one_time_keyboard=True, input_field_placeholder="Выберете дистанции"
		),
		)
	
	return DISTANCES
	
async def user_reg_distances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	user = update.message.from_user
	text = update.message.text

	# Если сообщение пользователя не было в клавиатуре, то это ответ на вопрос о факультете 
	if text not in cf.dist_personal_dict.keys() and text != cf.COMPLETE_CHOOSING:
		logger.info("Facility of %s, %s: %s", user.first_name, user.id, text)
		cf.users.user_dict.loc[user.id, 'Facility'] = text
	elif text != cf.COMPLETE_CHOOSING:
		logger.info("Dist of %s, %s: %s", user.first_name, user.id, text)
		if cf.users.user_dict.loc[user.id, text] == None:
			slot = None
			try:
				slot = cf.time_table_dict[text].booking_slot(rand = False,
															list_of_unavailable = cf.users.user_dict.loc[user.id, cf.users.RES_TIME ])
			
				cf.users.user_dict.loc[user.id, text] = slot[0]
				cf.users.user_dict.loc[user.id, cf.users.RES_TIME].append(slot[1:3])
				await update.message.reply_text(
				time.strftime("Ваше время старта на дистанции: %H:%M.\n", time.localtime(slot[1]))+
				"Пожалуйста, не опаздывайте;)"
				)

			except Exception as e:
				processing_exceptions(update.message, context, e)

		else:
			try:
				slot_num = cf.users.user_dict.loc[user.id, text]
				start_time = cf.time_table_dict[text].table[ slot_num ].start
				await update.message.reply_text(
					"Вы уже зарегистрированы на дистанцию "+ text + ".\n" +
					time.strftime("Старт в %H:%M.\n", time.localtime(start_time))
				
				)
			except Exception as e:
				processing_exceptions(update.message, context, e)

	else: 
		logger.info("User %s, %s finish the registration.", user.first_name)

	# cf.COMPLETE_CHOOSING означает выход.
	#
	# Доделать!!
	# Тут надо сделать отправку пользоветелю его данных и попросить согласие.
	if update.message.text == cf.COMPLETE_CHOOSING:
		await update.message.reply_text(
			"Спасибо!",
			reply_markup=ReplyKeyboardRemove(),
			)
		return ConversationHandler.END

	await update.message.reply_text(
		"На каких дистанциях вы хотели бы участвовать?",
		reply_markup=ReplyKeyboardMarkup(
		cf.dist_personal_keyboard, one_time_keyboard=True, input_field_placeholder="Выберете дистанции"
	),
	)
	return DISTANCES

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Cancels and ends the conversation."""
	user = update.message.from_user
	logger.info("User %s, %s canceled the conversation.", user.first_name, user.id)
	await update.message.reply_text(
		"Хорошо, поговорим потом!", reply_markup=ReplyKeyboardRemove()
	)

	return ConversationHandler.END
