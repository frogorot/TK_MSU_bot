import logging
import time
import pandas as pd

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

from telegram import (
	ReplyKeyboardMarkup, 
	ReplyKeyboardRemove, 
	InlineKeyboardButton, 
	InlineKeyboardMarkup, 
	Update,
	constants
	)
from telegram.ext import (
	Application,
	CommandHandler,
	ContextTypes,
	ConversationHandler,
	MessageHandler,
	JobQueue,
	filters,
)

import core_funcs as cf

from core_funcs import users

# Enable logging
logging.basicConfig(
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
	filename="logs\py_log"+ datetime.today().strftime("-%m.%d.%Y,%H-%M-%S") + ".log",filemode="w"
)
logger = logging.getLogger(__name__)

async def processing_exceptions(message, context: ContextTypes.DEFAULT_TYPE,  excep: Exception):

	print(excep.args)

	if excep.args[0] == "TimeTable.book_slot:: Nothing free.":
		await message.reply_text(
		"К сожалению, свободного времени не осталось.\n"
		"Пожалуйста, свяжитесь с начальником дистанции, возможно, он что-то придумает."
		)
	else:
		await message.reply_text(
		"Что-то пошло не так. Меня уже пытаются починить..."
		)

	for admin_chat_id in cf.admin_chat_id:
		await message.forward(chat_id= admin_chat_id, 
				   #from_chat_id= update.message.chat.id, 
				   disable_notification = True 
				   #message_id= update.message.message_id
				   )
		await context.bot.send_message(chat_id= admin_chat_id,
					text = excep.args)

###########################################
# Словарь задач
# Нужен чтобы отключать, запускать или менять задачи
WRITE_ALL_DATA_JOB = 'write_all_data_job'
NOTIFICATE_USER_JOB = 'notificate_user_job'
NOTIFICATE_TEAM_JOB = 'notificate_team_job'
job_dict = {}

def update_notification(context: ContextTypes.DEFAULT_TYPE):
	job_queue = context.job_queue
	try:
		for user in cf.users.user_dict.index:
			for dist_name in cf.dist_personal_dict:
				if pd.notna(cf.users.user_dict.at[user, dist_name]):
					if NOTIFICATE_USER_JOB + str(user) + dist_name not in job_dict:

						slot_num = int(cf.users.user_dict.at[user, dist_name])
						table = cf.time_table_dict[dist_name].table
						set_job_for_notify(user_id = user, 
							start_time =  table[slot_num].start,
							dist_name = dist_name,
							job_queue = job_queue)

			for dist_name in cf.dist_group_dict:
				if pd.notna(cf.users.user_dict.at[user, dist_name]):
					if NOTIFICATE_TEAM_JOB + str(user) + dist_name not in job_dict:

						slot_num = int(cf.users.user_dict.at[user, dist_name])
						table = cf.time_table_dict[dist_name].table

						set_job_for_notify(user_id = user, 
							start_time =  table[slot_num].start,
							dist_name = dist_name,
							job_queue = job_queue)
	except Exception as e:
		print(e.args)

def set_job_for_notify(user_id, start_time: int, dist_name, job_queue: JobQueue, members_id = []):

	raw_notif_time = start_time - 900 # уведомляем за 15 минут до старта
	notif_hour = int(raw_notif_time / 3600)
	notif_minute = int((raw_notif_time % 3600 ) / 60)
	notif_second = raw_notif_time % 60

	current_time = datetime.now()
	time_at_notify = current_time.replace(hour=notif_hour, minute=notif_minute, second=notif_second)
	
	job_name = NOTIFICATE_USER_JOB + str(user_id) + dist_name

	job_notificate_user =  job_queue.run_repeating(
		notificate_user,
		interval=600, 
		first=time_at_notify,
		#when = time_at_notify,
		name = job_name,
		chat_id = user_id,
		data = [dist_name, start_time]
		)
	job_dict[job_notificate_user.name] = job_notificate_user

	for member_id in  members_id:

		job_name = NOTIFICATE_TEAM_JOB + str(member_id) + dist_name

		job_notificate_user =  job_queue.run_repeating(
		notificate_user, 
		interval=600, 
		first=time_at_notify,
		#when = time_at_notify,
		name = job_name,
		chat_id = member_id,
		data = [dist_name, start_time]
		)
		job_dict[job_notificate_user.name] = job_notificate_user

async def notificate_user(context: ContextTypes.DEFAULT_TYPE):
	try:
		dist_name = context.job.data[0]
		start_time = context.job.data[1]
		job_dict[context.job.name].schedule_removal()

		await context.bot.send_message(
			chat_id=context.job.chat_id, 
			text=f'Напоминаю, на дистанции {dist_name} вы стартуете в: ' +
			time.strftime("%H:%M.\n", time.gmtime(start_time)) + 
			"Если вы передумали участвовать, напишите администартору: /ask_admin или сообщите начальнику дистанции")
	except Exception as e:
		print(e.args)

###########################################
# Несколько команд для админов
# 
# Принудительная загрузка
async def admin_forced_load(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
	await cf.load_all_data()

	user = update.message.from_user

	logger.info("Admin %s, %s initiate /forced_load", user.first_name, user.id)

	for admin_id in cf.admin_chat_id:
		await context.bot.send_message(chat_id=admin_id,
			text =  "Загрузил все файлы с диска.")

# Принудительное сохранение
async def admin_forced_write(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
	await cf.write_all_data(None)

	user = update.message.from_user
	logger.info("Admin %s, %s initiate /forced_write", user.first_name, user.id)

	for admin_id in cf.admin_chat_id:
		await context.bot.send_message(chat_id=admin_id,
			text =  "Сохранил все файлы на диск")

# Остановка периодических сохранений
async def admin_stop_writes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
	job_dict[WRITE_ALL_DATA_JOB].enabled = False

	user = update.message.from_user
	logger.info("Admin %s, %s initiate /stop_writes", user.first_name, user.id)

	for admin_id in cf.admin_chat_id:
		await context.bot.send_message(chat_id=admin_id,
			text =  "Остановил периодическое сохранение.")

# Запуск периодических сохранений
async def admin_start_writes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
	job_dict[WRITE_ALL_DATA_JOB].enabled = True

	user = update.message.from_user
	logger.info("Admin %s, %s initiate /start_writes", user.first_name, user.id)

	for admin_id in cf.admin_chat_id:
		await context.bot.send_message(chat_id=admin_id,
			text =  "Запустил периодическое сохранение.")

# Отправка актуальной версии протоколов.
async def admin_send_all_data(update: Update, context: ContextTypes.DEFAULT_TYPE):

	user = update.message.from_user
	logger.info("Admin %s, %s initiate /send_all_data", user.first_name, user.id)

	admin_id = update.message.from_user.id
	try:
		for dist_name in cf.dist_personal_dict:
			with open(cf.time_table_dict[dist_name].retun_filename(), 'rb') as file:
				await context.bot.send_document(chat_id = admin_id,
								 document = file)
			with open(cf.dist_personal_dict[dist_name].retun_filename(), 'rb') as file:
				await context.bot.send_document(chat_id = admin_id,
								 document = file)

		for dist_name in cf.dist_group_dict:
			with open(cf.time_table_dict[dist_name].retun_filename(), 'rb') as file:
				await context.bot.send_document(chat_id = admin_id,
								 document = file)
			with open(cf.dist_group_dict[dist_name].retun_filename(), 'rb') as file:
				await context.bot.send_document(chat_id = admin_id,
								 document = file)

		with open(cf.users.retun_filename(), 'rb') as file:
			await context.bot.send_document(chat_id = admin_id,
								 document = file)

		with open(cf.judges.retun_filename(), 'rb') as file:
			await context.bot.send_document(chat_id = admin_id,
								 document = file)

		with open(cf.teams.retun_filename(), 'rb') as file:
			await context.bot.send_document(chat_id = admin_id,
								 document = file)
	except Exception as e:
		print(e.args)

###########################################
# Handle '/help'
# Дописать!!
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):

	await context.bot.send_message(chat_id=update.effective_chat.id,
	text =  """
Привет! Я бот горного Турклуба МГУ. Я совсем маленький, но быстро учусь!
Мои команды:
<i>/start</i> - Регистрация участника на слёт. Во время регистрации можно выбрать интересующие вас _личные_ дистанции.
<i>/new_team</i> - Регистрация команды на командную дистанцию. На каждую дистанцию регистрируется отдельная команда.
<i>/my_dist</i> - Список дистанций (как личных, так и командных, на которые вы зарегистрированы.
<i>/new_dist</i> - Зарегистрироваться ещё на какие-то личные дистанции.
<i>/ask_admin</i> - Написанное после этой команды сообщение будет передано администратору. Может пригодится для связи по проблемам или предложениям и замечаниям.
""",
parse_mode = constants.ParseMode('HTML')
)
	#bot.register_next_step_handler(msg, process_name_step)

###########################################
# Handle '/ask_admin'
MESSAGE_TO_ADMIN = 0
async def process_ask_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text(
	   'Пожалуйста, введите сообщение для Администратора.'
	)
	return MESSAGE_TO_ADMIN

async def process_send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

	user = update.message.from_user
	logger.info("User %s, %s send something to admin", user.first_name, user.id)

	await update.message.reply_text(
	   'Ваше сообщение передано Администратору.'
	)
	if update.message.chat.has_protected_content or update.message.has_protected_content:
		print("Unavalable")

	for admin_chat_id in cf.admin_chat_id:
		await update.message.forward(chat_id= admin_chat_id, 
					   #from_chat_id= update.message.chat.id, 
					   disable_notification = True 
					   #message_id= update.message.message_id
					   )
	return ConversationHandler.END

###########################################
#Handle my_dist

async def user_print_dist(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.message.from_user.id
	
	user = update.message.from_user
	logger.info("User %s, %s asks about his distances", user.first_name, user.id)

	text = ""

	for dist_name in cf.time_table_dict:
		if pd.notna(cf.users.user_dict.at[user_id, dist_name]):
			slot_num = int(cf.users.user_dict.at[user_id, dist_name])
			slot_start_time = cf.time_table_dict[dist_name].table[slot_num].start
			text += "На дистанции: <b>" + dist_name + time.strftime("</b> вы стартуете в: <b>%H:%M</b>.\n", time.gmtime(slot_start_time)) 
			text += "Номер слота: " + str(slot_num) + ".\n"
	
	if text == "":
		text = "Вы не зарегистрировались ни на одной дистанции." 
	text += "\nПриятного участия!!"
	await update.message.reply_text(
		text = text,
		parse_mode = constants.ParseMode('HTML')
		)

###########################################
#Handle new_dist
#
#user registration steps:
AGE, GENDER, UNIVERSITY, FACILITY, DISTANCES = range(5)

async def user_new_dist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	user = update.message.from_user
	text = update.message.text
	users_data = cf.users.user_dict
	try:
		if user.id not in users_data.index:
			await update.message.reply_text(
				"Пожалуйста, сначала зарегистрируйтесь."
			)
			return ConversationHandler.END
	except Exception as e:
		await processing_exceptions(update.message, context, e)

	if text not in cf.dist_personal_dict.keys() and text != cf.COMPLETE_CHOOSING:
		logger.info("Wrong Dist of %s, %s: %s", user.first_name, user.id, text)
		await update.message.reply_text(
			"Такой дистанции нет.\n"
			"На каких дистанциях вы хотели бы участвовать?"
			"Если вы выбрали всё, что хотели, нажмите \"" + COMPLETE_CHOOSING + "\" чтобы завершить регистрацию.",
			reply_markup=ReplyKeyboardMarkup(
				cf.dist_personal_keyboard, 
				one_time_keyboard=True, 
				input_field_placeholder="Выберите дистанцию"
			),
		)
		return DISTANCES

	elif text != cf.COMPLETE_CHOOSING:
		logger.info("Dist of %s, %s: %s", user.first_name, user.id, text)
		if pd.isna(users_data.loc[user.id, text]):
			slot = None
			try:
				slot = cf.time_table_dict[text].booking_slot(rand = False,
															list_of_unavailable = users_data.loc[user.id, cf.users.RES_TIME ])
				
				users_data.at[user.id, text] = slot[0]
				users_data.at[user.id, cf.users.RES_TIME].append(slot[1:3])


				set_job_for_notify(user_id = user.id, 
					   start_time = slot[0], 
					   dist_name = text,
					   job_queue = context.job_queue)

				await update.message.reply_text(
				time.strftime("Ваше время старта на дистанции: %H:%M.\n", time.gmtime(slot[1]))+
				"Номер слота: " + str(int(slot[0])) + ".\n"
				"Пожалуйста, не опаздывайте;)"
				)

			except Exception as e:
				await processing_exceptions(update.message, context, e)
				
		else:
			try:
				slot_num = int(users_data.at[user.id, text])
				start_time = cf.time_table_dict[text].table[ slot_num ].start
				await update.message.reply_text(
					"Вы уже зарегистрированы на дистанцию "+ text + ".\n" +
					time.strftime("Старт в %H:%M.\n", time.gmtime(start_time))
				
				)
			except Exception as e:
				await processing_exceptions(update.message, context, e)

	else: 
		logger.info("User %s, %s finish the registration.", user.first_name, user.id)

		# cf.COMPLETE_CHOOSING означает выход.
		#
		# Доделать!!
		# Тут надо сделать отправку пользоветелю его данных и попросить согласие.
		if update.message.text == cf.COMPLETE_CHOOSING:
			await user_print_dist(update, context)

			return ConversationHandler.END

	await update.message.reply_text(
		"На каких дистанциях вы хотели бы участвовать?"
		"Если вы выбрали всё, что хотели, нажмите \"" + COMPLETE_CHOOSING + "\" чтобы завершить регистрацию.",
		reply_markup=ReplyKeyboardMarkup(
			cf.dist_personal_keyboard, 
			one_time_keyboard=True, 
			input_field_placeholder="выберите дистанции"
	),
	)
	return DISTANCES

###########################################
#Handle user_reg
#
#user registration steps:
AGE, GENDER, UNIVERSITY, FACILITY, DISTANCES = range(5)

async def user_reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Starts the conversation and asks the user about their name."""
	try:
		user_id = update.message.from_user.id
		user = update.message.from_user
		#for data in cf.users.user_dict.loc[user_id, 'Tg_id':cf.Users.RES_TIME]:
		#	cf.users.user_dict.loc[user_id, col] = None
		
		cf.users.user_dict.at[user_id, 'Tg_id'] = user_id
		cf.users.user_dict.at[user_id, cf.users.RES_TIME] = []
		cf.users.user_dict.at[user_id, 'Facility'] = None 

		logger.info("Start reg %s, %s", user.first_name, user.id)

		await update.message.reply_text(
		   "Ура, давайте знакомится!\n\n"
	   "Ваш id:  " + str(update.message.from_user.id) + ".\nОн может понадобится для общения со мной.\n\n"
	   "Отправьте /cancel чтобы прекратить общение.\n\n"
	   "За 15 минут до старта любой дистанции, которую вы выберите, вам придёт напоминание.\n\n"
	   "Как вас зовут? Пожалуйста, напишите полные имя и фамилию.",
		)
	except Exception as e:
		await processing_exceptions(update.message, context, e)

	return AGE

async def user_reg_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Stores the selected name and asks for a age."""
	user = update.message.from_user
	logger.info("Name of %s, %s: %s", user.first_name, user.id, update.message.text)
	if all(x.isalpha() or x.isspace() for x in update.message.text):
		cf.users.user_dict.loc[user.id, 'Name'] = update.message.text
		await update.message.reply_text(
		"Приятно познакомится! "
		"Сколько вам лет?"
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
				"Пожалуйста, выберите ваш пол.",
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

async def user_reg_facility(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Stores the selected university and asks for a facility or for distances."""
	user = update.message.from_user
	logger.info("Univer of %s, %s: %s", user.first_name, user.id,update.message.text)
	
	cf.users.user_dict.loc[user.id, 'University'] = update.message.text

	is_msu = re.search("МГУ", update.message.text, re.IGNORECASE)
	if is_msu != None:
		await update.message.reply_text(
			"На каком факультете вы учитесь? "
		)
		#return DISTANCES
	else:
		await update.message.reply_text(
			"На каких дистанциях вы хотели бы участвовать?"
			"Если вы выбрали всё, что хотели, нажмите \"" + cf.COMPLETE_CHOOSING + "\" чтобы завершить регистрацию.",
			reply_markup=ReplyKeyboardMarkup(
			cf.dist_personal_keyboard, one_time_keyboard=True, input_field_placeholder="выберите дистанции"
		),
		)
	
	return DISTANCES
	
async def user_reg_distances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	user = update.message.from_user
	text = update.message.text
	users_data = cf.users.user_dict

	# Если сообщение пользователя не было в клавиатуре, то это ответ на вопрос о факультете 
	if text not in cf.dist_personal_dict.keys() and text != cf.COMPLETE_CHOOSING:
		logger.info("Facility of %s, %s: %s", user.first_name, user.id, text)
		users_data.loc[user.id, 'Facility'] = text
	elif text != cf.COMPLETE_CHOOSING:
		logger.info("Dist of %s, %s: %s", user.first_name, user.id, text)
		if pd.isna(users_data.loc[user.id, text]):
			slot = None
			try:
				slot = cf.time_table_dict[text].booking_slot(rand = False,
															list_of_unavailable = users_data.loc[user.id, cf.users.RES_TIME ])
				
				users_data.at[user.id, text] = slot[0]
				users_data.at[user.id, cf.users.RES_TIME].append(slot[1:3])

				set_job_for_notify(user_id = user.id, 
					   start_time = slot[0], 
					   dist_name = text,
					   job_queue = context.job_queue)

				await update.message.reply_text(
				time.strftime("Ваше время старта на дистанции: %H:%M.\n", time.gmtime(slot[1]))+ 
				"Номер слота: " + str(int(slot[0])) + ".\n"
				"Пожалуйста, не опаздывайте;)"
				)

			except Exception as e:
				await processing_exceptions(update.message, context, e)

		else:
			try:
				slot_num = int(users_data.at[user.id, text])
				start_time = cf.time_table_dict[text].table[ slot_num ].start
				await update.message.reply_text(
					"Вы уже зарегистрированы на дистанцию "+ text + ".\n" +
					time.strftime("Старт в %H:%M.\n", time.gmtime(start_time))
				
				)
			except Exception as e:
				await processing_exceptions(update.message, context, e)

	else: 
		logger.info("User %s, %s finish the registration.", user.first_name, user.id)

	# cf.COMPLETE_CHOOSING означает выход.
	#
	# Доделать!!
	# Тут надо сделать отправку пользоветелю его данных и попросить согласие.
		if update.message.text == cf.COMPLETE_CHOOSING:
			facil = ""
			if users_data.at[user.id, 'Facility'] != None :
				facil = "Вы имеете отношение факультету: " + users_data.at[user.id, 'Facility'] + "\n"

			await update.message.reply_text(
				"Спасибо!\n\n"
				"Вас зовут: " + users_data.at[user.id, 'Name'] + "\n"
				"Вам: " + str(users_data.at[user.id, 'Age']) + " лет\n"
				"Вы: " + users_data.at[user.id, 'Sex'] + "\n"
				"Вы учитесь/работаете в: " + users_data.at[user.id, 'University'] + "\n" + 
				facil,
				reply_markup=ReplyKeyboardRemove(),
				)

			await user_print_dist(update, context)

			await update.message.reply_text(
				"Если что-то не верно, просто снова вбейте /start и повторите регистрацию!"
				)
			return ConversationHandler.END

	await update.message.reply_text(
		"На каких дистанциях вы хотели бы участвовать?"
		"Если вы выбрали всё, что хотели, нажмите \"" + cf.COMPLETE_CHOOSING + "\" чтобы завершить регистрацию.",
		reply_markup=ReplyKeyboardMarkup(
			cf.dist_personal_keyboard, 
			one_time_keyboard=True, 
			input_field_placeholder="выберите дистанции"
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

###########################################
#Handle team_reg
#user registration steps:
DIST, NAME, MEMBERS_ADD, CONFIRM  = range(4)

async def team_reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Starts the conversation and asks the user about team name."""

	user_id = update.message.from_user.id

	user = update.message.from_user
	logger.info("User %s, %s start reg team", user.first_name, user.id)

	await update.message.reply_text(
	   "Сейчас зарегистрируем новую команду!\n"
	   "Приготовьте id (именно id, а не @username; я печатал его, когда вы регистрировались) ваших товарищей.\n"
	   "Вашим товарищам останется только подтвердить участие. \n"
	   "Обязательно отправьте /cancel чтобы остановить регистрацию. Иначе я сломаюсь( \n\n"
	   "На какую дистанцию вы регистрируете команду?",
	   reply_markup=ReplyKeyboardMarkup(
		cf.dist_group_keyboard, one_time_keyboard=True, input_field_placeholder="выберите дистанции"
	),
	)
	return DIST

async def team_reg_dist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Starts the conversation and asks the user about distance."""

	user_id = update.message.from_user.id
	dist = update.message.text
	# При регистрации команды всем участникам пишется слот команды.
	try:
		if pd.notna(cf.users.user_dict.at[user_id, dist]):
			slot_num = int(cf.users.user_dict.at[user_id, dist])
			slot_start_time = cf.time_table_dict[dist].table[slot_num].start

			user = update.message.from_user
			logger.info("Team_reg: his also take part in this dist. User %s, %s", user.first_name, user.id)

			await update.message.reply_text(
				"Вы уже состоите в команде, зарегистрированной, на эту дистанцию." +
				time.strftime("Стартуете в: %H:%M.\n", time.gmtime(slot_start_time)) +
				"На какую дистанцию вы регистрируете команду?",
				reply_markup=ReplyKeyboardMarkup(
					cf.dist_group_keyboard, 
					one_time_keyboard=True, 
					input_field_placeholder="выберите дистанции"
				)
			)
			return None
	except Exception as e:
		processing_exceptions(update.message, context, e)

	#cf.teams.team_dict.at[(user_id, dist), 'Tg_id_major'] = user_id
	cf.teams.team_dict.at[(user_id, dist), 'Distance'] = dist

	user = update.message.from_user
	logger.info("Team_reg: User %s, %s chose dist: %s", user.first_name, user.id, dist)

	await update.message.reply_text(
	   "Как будет называться команда?\n"
	)
	return NAME

#служебная функция для обнаружения названия дистанции
def find_dist_name(user_id) -> str:
	"""Asks the user about team name."""
	dist_name = None
	for try_dist_name in cf.dist_group_dict.keys():
		if pd.notna(cf.teams.team_dict.at[(user_id, try_dist_name), 'Distance']):
			dist_name = try_dist_name
			break
	else:
		raise Exception("team_reg_name: Can not find index in dist_group_dict")
	# Если ничего не нашли он остался None
	return dist_name

async def team_reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Asks the user about members id."""

	user = update.message.from_user
	user_id = user.id

	name = update.message.text

	try:
		dist = find_dist_name(user_id)
	
		if name in list(cf.teams.team_dict.xs(dist, level='Distance').loc[:,'Name'] ):

			logger.info("Team_reg: This name is also exsits. User %s, %s, name: %s", user.first_name, user.id, name)

			await update.message.reply_text(
				"Команда с таким именем уже зарегистрирована, придумайте другое.\n"
				"Как будет называться команда?\n"
			)
			return NAME

	except Exception as e:
		processing_exceptions(update.message, context, e)

	if len(name) > cf.TEAM_NAME_LENTH:

		logger.info("Team_reg: Too long name. User %s, %s, name: %s", user.first_name, user.id, name)

		await update.message.reply_text(
			"Можно, пожалуйста, покороче?"
			"Я больше " + str(TEAM_NAME_LENTH) + "букв не запомню("
			)
		return NAME
	else:
		cf.teams.team_dict.loc[(user_id, dist), 'Name'] = name

		logger.info("Team_reg: User %s, %s, chose name: %s", user.first_name, user.id, name)

		await update.message.reply_text(
			"В команде должно быть " + str(cf.dist_group_team_members_count[dist]) + " участников. \n"
			"Пожалуйста, напишите id нового участника команды. \n" 
			"Я печатаю id в ответ на вашу первую команду."
			)
		return MEMBERS_ADD

async def team_reg_add_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Asks the user about team name."""

	cf.teams.team_dict.loc[(user_id, dist),'Member_confurm_num'] = 1
	cf.teams.team_dict.at[(user_id, dist), cf.Teams.MEMBERS_ID] = []

	major_id = update.message.from_user.id
	dist = find_dist_name(major_id)

	if not update.message.text.isdigit():

		logger.info("Team_reg: User %s, %s, print bad id: %s", user.first_name, user.id, update.message.text)

		await update.message.reply_text(
			"ID телеграмма состоит только из цифр, пожалуйста, напишите правильный id.\n\n"
			"В команде должно быть " + str(cf.dist_group_team_members_count[dist]) + " участников. \n"
			"Пожалуйста, напишите id нового участника команды." 
			)
		return MEMBERS_ADD

	new_member_id = int(update.message.text)

	# Проверка, есть ли такой id в зарегистрированных
	if new_member_id not in cf.users.user_dict.index or pd.isna(cf.users.user_dict.at[new_member_id, 'Name']):

		logger.info("Team_reg: User %s, %s, print unknown id: %s", user.first_name, user.id, new_member_id)

		await update.message.reply_text(
			"Я не знаком с таким человеком( Он точно регистрировался у меня?\n"
			"Если у вашего знакомого нет Телеграмм, то попросите главного судью любой дистанции - они вам помогут.\n\n"
			"В команде должно быть " + str(cf.dist_group_team_members_count[dist]) + " участников. \n"
			"Пожалуйста, напишите id нового участника команды." 
			)
		return MEMBERS_ADD

	# Обработка id, если он найден
	elif pd.notna(cf.users.user_dict.at[new_member_id, dist]):

		logger.info("Team_reg: User %s, %s, print id, that also take part in dist: %s", user.first_name, user.id, new_member_id)

		await update.message.reply_text(
			"Этот участник уже зарегистрирован в другой команде.\n"
			"В команде должно быть " + str(cf.dist_group_team_members_count[dist]) + " участников. \n"
			"Пожалуйста, напишите id нового участника команды." 
			)
		return MEMBERS_ADD
	elif new_member_id == major_id or new_member_id in cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID]:

		logger.info("Team_reg: User %s, %s, print id, that also take part in dist: %s", user.first_name, user.id, new_member_id)

		await update.message.reply_text(
			"Этот участник уже в вашей команде.\n"
			"В команде должно быть " + str(cf.dist_group_team_members_count[dist]) + " участников. \n"
			"Пожалуйста, напишите id нового участника команды." 
			)
		return MEMBERS_ADD

	else:
		try:
			cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID].append(new_member_id)
			new_member_num = len(cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID])
			num_of_remaining_members = cf.dist_group_team_members_count[dist] - 1 - new_member_num


		except Exception as e:
			processing_exceptions(update.message, context, e)


		# Записали id всех участников
		if num_of_remaining_members == 0:

			logger.info("Team_reg: User %s, %s, team reg complete. dist:", user.first_name, user.id, dist)

			await update.message.reply_text(
			"Команда " + cf.teams.team_dict.at[(major_id, dist), 'Name'] + " зарегистрирована.\n"
			"Участникам отправлены запросы на подтверждение. Как только я получу все подтверждения, сразу извещу вас."
			"Время старта пришлю тогда же"
			)
			# Отправляем запросы на подтверждение
			major_name = cf.users.user_dict.at[major_id, 'Name']
			members_list = ""
			try:
				for member_id in cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID]:
					member_name = cf.users.user_dict.at[member_id, 'Name']
					members_list += member_name + "\n"
				members_list = major_name + "  - Зарегистрировал команду\n" + members_list

				for member_id in cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID]:
					
					# не знаю, насколько это красиво, но тогда по нажатию на кнопку я получу всю информацию.
					keyboard = [
							[
						    InlineKeyboardButton("Согласен", 
							   callback_data= cf.TEAM_REG_PREFIX + str(major_id) + "|" + dist + "Y"),
						    InlineKeyboardButton("Не согласен", 
							   callback_data= cf.TEAM_REG_PREFIX + str(major_id) + "|" + dist + "N"),
						] ]
					reply_markup = InlineKeyboardMarkup(keyboard)

					await context.bot.send_message( chat_id= member_id,
						text  = 
						"Вы согласны участвовать в команде " + cf.teams.team_dict.loc[(major_id, dist), 'Name'] + ",\n"
						"На дистанции " + cf.teams.team_dict.loc[(major_id, dist), 'Distance'] + ",\n"
						"В составе:" + members_list + "?",
						reply_markup= reply_markup
						)
				return ConversationHandler.END
			except Exception as e:
				processing_exceptions(update.message, context, e)

		# Ещё не все участники записаны
		else:
			await update.message.reply_text(
				"В команде должно быть ещё" + str(num_of_remaining_members) + " участника. \n"
				"Пожалуйста, напишите id нового участника команды. \n" 
				"Я печатаю id в ответ на вашу первую команду."
				)
			return MEMBERS_ADD

async def team_reg_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	query = update.callback_query
	data = query.data
	id_size = data.find('|')

	len_of_tem_prefix = len(cf.TEAM_REG_PREFIX)
	major_id = int(data[len_of_tem_prefix : id_size])
	dist = data[id_size + 1 : -1]
	mean = data[-1]

	major_name = cf.users.user_dict.loc[major_id, 'Name']
	members_list = ""
	for member_id in cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID]:
		member_name = cf.users.user_dict.at[member_id, 'Name']
		members_list += member_name + "\n"
	members_list = major_name + "  - Зарегистрировал команду\n" + members_list

	try:
		if mean == "Y":

			logger.info("Team_reg: User %s, %s, confurm to take part in dist: %s, major_id: %s", user.first_name, user.id, dist, major_id)

			cf.teams.team_dict.loc[(major_id, dist),'Member_confurm_num'] += 1
			await query.edit_message_text(text="Спасибо! Как только я получу все подтверждения, то сразу подберу вам время старта.")

			# Назначаем время старта
			if cf.teams.team_dict.at[(major_id, dist),'Member_confurm_num'] == cf.dist_group_team_members_count[dist]:
				
				# Собираем список занятых времён
				unawalable_list = cf.users.user_dict.loc[major_id, cf.Users.RES_TIME]

				for member_id in cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID]:
					member_unw_list = cf.users.user_dict.loc[member_id, cf.Users.RES_TIME]
					for pair in member_unw_list:
						unawalable_list.append(pair)
				
				# Выбираем слот
				try:
					slot = cf.time_table_dict[dist].booking_slot(rand = False,
																list_of_unavailable = unawalable_list)
				except Exception as ex:
					processing_exceptions(update.message, context, e)

				logger.info("Team_reg: dist: %s, major_id: %s; slot num: start time: ", 
									dist, 
									major_id, 
									slot[0], 
									time.strftime("%H:%M.\n", time.gmtime(slot[1])))

				# Назначаем слот команде
				cf.teams.team_dict.loc[(major_id, dist), 'Slot_num'] = slot[0]

				set_job_for_notify(user_id = major_id, 
					   start_time = slot[0], 
					   dist_name = dist,
					   job_queue = context.job_queue,
					   members_id=cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID])

				# Добавляем время нахождения на дистанции к занятому времени у всех участников.
				# Оповещаем участников о успешной регистрации
				for member_id in cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID] + [major_id]:
					#member_id = cf.teams.team_dict.loc[(major_id, dist), member_column]
					cf.users.user_dict.loc[member_id, cf.Users.RES_TIME].append(slot[1:3])
					cf.users.user_dict.at[member_id, dist] = slot[0]
					await context.bot.send_message(
						chat_id = member_id, 
						text = "Вы в команде: " + cf.teams.team_dict.loc[(major_id, dist), 'Name'] + ",\n"
								"На дистанции: " + cf.teams.team_dict.loc[(major_id, dist), 'Distance'] + ",\n"
								"В составе:" + members_list + "\n" +
								time.strftime("Стартуете в: %H:%M.\n", time.gmtime(slot[1]))+
								"Номер слота - " + str(slot[0]) + ".\n" +
								"Пожалуйста, не опаздывайте;)"
						)
			return ConversationHandler.END


		else:
		#Оповещаем всех об отмене, сбрасываем команду.
			
			logger.info("Team_reg: User %s, %s,  NOT confurm to take part in dist: %s, major_id: %s", user.first_name, user.id, dist, major_id)

			for member_id in cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID] + [major_id]:
				#member_id = cf.teams.team_dict.loc[(major_id, dist), member_column]
				await context.bot.send_message( chat_id= member_id,
				text  = 
				"Кто-то не соглаcен участвовать в команде " + cf.teams.team_dict.loc[(major_id, dist), 'Name'] + ",\n"
				"На дистанции " + cf.teams.team_dict.loc[(major_id, dist), 'Distance'] + ",\n"
				"В составе:" + members_list + "\n"
				"Я вынужден отменить регистрацию команды."
					)

			cf.teams.team_dict = cf.teams.team_dict.drop(index=(major_id, dist))

			return ConversationHandler.END
	except Exception as e:
		processing_exceptions(update.message, context, e)
