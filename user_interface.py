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

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update
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

###########################################
# Словарь задач
# Нужен чтобы отключать, запускать или менять задачи
WRITE_ALL_DATA_JOB = 'write_all_data_job'
job_dict = {}


###########################################
# Несколько команд для админов
# 
# Принудительная загрузка
async def admin_forced_load(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
	await cf.load_all_data()

	for admin_id in cf.admin_chat_id:
		await context.bot.send_message(chat_id=admin_id,
			text =  "Загрузил все файлы с диска.")

# Принудительное сохранение
async def admin_forced_write(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
	await cf.write_all_data()

	for admin_id in cf.admin_chat_id:
		await context.bot.send_message(chat_id=admin_id,
			text =  "Сохранил все файлы на диск")

# Остановка периодических сохранений
async def admin_stop_writes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
	job_dict[WRITE_ALL_DATA_JOB].enabled = False

	for admin_id in cf.admin_chat_id:
		await context.bot.send_message(chat_id=admin_id,
			text =  "Остановил периодическое сохранение.")

# Запуск периодических сохранений
async def admin_start_writes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
	job_dict[WRITE_ALL_DATA_JOB].enabled = True

	for admin_id in cf.admin_chat_id:
		await context.bot.send_message(chat_id=admin_id,
			text =  "Запустил периодическое сохранение.")

# Отправка актуальной версии протоколов.
async def admin_send_all_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
/start - Регистрация участника на слёт. Во время регистрации можно выбрать интересующие вас _личные_ дистанции.
/new_team - Регистрация команды на командную дистанцию. На каждую дистанцию регистрируется отдельная команда.
/my_dist - Список дистанций (как личных, так и командных, на которые вы зарегистрированы.
/ask_admin - Написанное после этой команды сообщение будет передано администратору. Может пригодится для связи по проблемам или предложениям и замечаниям.
""")
	#bot.register_next_step_handler(msg, process_name_step)


async def processing_exceptions(message, context: ContextTypes.DEFAULT_TYPE,  excep: Exception):

	print('Что-то пошло не так( Попробуйте ещё раз! ')
	print(excep.args)
	for admin_chat_id in cf.admin_chat_id:
		await message.forward(chat_id= admin_chat_id, 
				   #from_chat_id= update.message.chat.id, 
				   disable_notification = True 
				   #message_id= update.message.message_id
				   )
		await context.bot.send_message(chat_id= admin_chat_id,
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
	
	text = ""

	for dist_name in cf.time_table_dict:
		if pd.notna(cf.users.user_dict.at[user_id, dist_name]):
			slot_num = int(cf.users.user_dict.at[user_id, dist_name])
			slot_start_time = cf.time_table_dict[dist_name].table[slot_num].start
			text += "На дистанци: " + dist_name + time.strftime(" вы стартуете в: %H:%M.\n", time.localtime(slot_start_time)) 

	text += "\nПриятного участия!!"
	await update.message.reply_text(
		text = text
		)

###########################################
#Handle user_reg
#
#user registration steps:
AGE, GENDER, UNIVERSITY, FACILITY, DISTANCES = range(5)

async def user_reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Starts the conversation and asks the user about their name."""

	user_id = update.message.from_user.id
	for col in cf.users.user_dict.columns:
		cf.users.user_dict.loc[user_id, col] = None
	cf.users.user_dict.loc[user_id, 'Tg_id'] = user_id
	cf.users.user_dict.at[user_id, cf.users.RES_TIME] = []

	await update.message.reply_text(
	   "Ура, давайте знакомится!\n\n"
	   "Ваш id:  " + str(update.message.from_user.id) + ".\nОн может понадобится для общения со мной.\n\n"
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
			"На каких дистанциях вы хотели бы участвовать?",
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
				await update.message.reply_text(
				time.strftime("Ваше время старта на дистанции: %H:%M.\n", time.localtime(slot[1]))+
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
					time.strftime("Старт в %H:%M.\n", time.localtime(start_time))
				
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
		await update.message.reply_text(
			"Спасибо!",
			reply_markup=ReplyKeyboardRemove(),
			)
		return ConversationHandler.END

	await update.message.reply_text(
		"На каких дистанциях вы хотели бы участвовать?",
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
	#for col in cf.teams.team_dict.columns:
	#	cf.teams.team_dict.columns[user_id, col] = None
	#cf.users.user_dict.loc[user_id, 'Tg_id'] = user_id
	#cf.users.user_dict.loc[user_id, cf.users.RES_TIME] = []

	await update.message.reply_text(
	   "Сейчас зарегистрируем новую команду!\n"
	   "Приготовьте id (именно id, а не @username; я печатал его, когда вы регистрировались) выших товарищей.\n"
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
			await update.message.reply_text(
				"Вы уже состоите в команде, зарегистрированной, на эту дистанцию." +
				time.strftime("Стартуете в: %H:%M.\n", time.localtime(slot_start_time)) +
				"На какую дистанцию вы регистрируете команду?",
				reply_markup=ReplyKeyboardMarkup(
					cf.dist_group_keyboard, 
					one_time_keyboard=True, 
					input_field_placeholder="выберите дистанции"
				)
			)
			return None
	except Exception as e:
		print(e.args)

	#cf.teams.team_dict.at[(user_id, dist), 'Tg_id_major'] = user_id
	cf.teams.team_dict.at[(user_id, dist), 'Distance'] = dist

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

	user_id = update.message.from_user.id
	name = update.message.text

	try:
		dist = find_dist_name(user_id)
	
	
		print(cf.teams.team_dict.xs(dist, level='Distance'))
		if name in list(cf.teams.team_dict.xs(dist, level='Distance').loc[:,'Name'] ):
			await update.message.reply_text(
				"Команда с таким именем уже зарегистрирована, придумайте другое.\n"
				"Как будет называться команда?\n"
			)
			return NAME

	except Exception as e:
		print(e.args)

	if len(name) > cf.TEAM_NAME_LENTH:
		await update.message.reply_text(
			"Можно, пожалуйста, покороче?"
			"Я больше " + str(TEAM_NAME_LENTH) + "букв не запомню("
			)
		return NAME
	else:
		cf.teams.team_dict.loc[(user_id, dist), 'Name'] = name
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
		await update.message.reply_text(
			"ID телеграмма состоит только из цифр, пожалуйста, напишите правильный id.\n\n"
			"В команде должно быть " + str(cf.dist_group_team_members_count[dist]) + " участников. \n"
			"Пожалуйста, напишите id нового участника команды." 
			)
		return MEMBERS_ADD

	new_member_id = int(update.message.text)

	# Проверка, есть ли такой id в зарегистрированных
	if new_member_id not in cf.users.user_dict.index or pd.isna(cf.users.user_dict.at[new_member_id, 'Name']):
		await update.message.reply_text(
			"Я не знаком с таким человеком( Он точно регистрировался у меня?\n"
			"Если у вашего знакомого нет Телеграмм, то попросите главного судью любой дистанции - они вам помогут.\n\n"
			"В команде должно быть " + str(cf.dist_group_team_members_count[dist]) + " участников. \n"
			"Пожалуйста, напишите id нового участника команды." 
			)
		return MEMBERS_ADD

	# Обработка id, если он найден
	elif pd.notna(cf.users.user_dict.at[new_member_id, dist]):
		await update.message.reply_text(
			"Этот участник уже зарегистрирован в другой команде.\n"
			"В команде должно быть " + str(cf.dist_group_team_members_count[dist]) + " участников. \n"
			"Пожалуйста, напишите id нового участника команды." 
			)
		return MEMBERS_ADD
	elif new_member_id == major_id or new_member_id in cf.teams.team_dict.at[(major_id, dist), cf.Teams.MEMBERS_ID]:
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
			print(e.args)


		# Записали id всех участников
		if num_of_remaining_members == 0:
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
				print(e.args)

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


				# Назначаем слот команде
				cf.teams.team_dict.loc[(major_id, dist), 'Slot_num'] = slot[0]
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
								time.strftime("Стартуете в: %H:%M.\n", time.localtime(slot[1]))+
								"Номер слота - " + str(slot[0]) + ".\n" +
								"Пожалуйста, не опаздывайте;)"
						)
			return ConversationHandler.END


		else:
		#Оповещаем всех об отмене, сбрасываем команду.
		
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
		print(e.args)
