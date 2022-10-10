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

from core_funcs import users


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


def processing_exceptions(message, context: ContextTypes.DEFAULT_TYPE,  excep: Exception):

	print('Что-то пошло не так( Попробуйте ещё раз! ')
	print(excep.args)
	for admin_chat_id in cf.admin_chat_id:
		message.forward(chat_id= admin_chat_id, 
				   #from_chat_id= update.message.chat.id, 
				   disable_notification = True 
				   #message_id= update.message.message_id
				   )
		context.bot.send_message(chat_id= admin_chat_id,
					text = excep.args)

MESSAGE_TO_ADMIN = 0
# Handle '/ask_admin'
#@bot.message_handler(commands=['ask_admin'])
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
	try:

		await update.message.forward(chat_id= cf.admin_chat_id, 
					   #from_chat_id= update.message.chat.id, 
					   disable_notification = True 
					   #message_id= update.message.message_id
					   )
	except Exception as ex:
		processing_exceptions(update.message, ex)
	return ConversationHandler.END

async def user_reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Starts the conversation and asks the user about their name."""
	await update.message.reply_text(
	   "Ура, давайте знакомится!\n"
	   "Ваш id:  " + str(update.message.from_user.id) + ". Он может понадобится для общения со мной.\n"
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
	else:
		await update.message.reply_text(
			"Пожалуйста, напишите имя и фамилию."
			"Для этого вам нужны только буквы и пробелы ;)"
		)
		return None # При возврате None  остаётся текущее состояние.
	
async def user_reg_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Stores the selected age and asks for a gender."""
	user = update.message.from_user
	logger.info("Age of %s: %s", user.first_name, update.message.text)

	reply_keyboard = [["Мальчик", "Девочка"]]
	
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
	text = update.message.text
	users_data = cf.users.user_dict

	# Если сообщение пользователя не было в клавиатуре, то это ответ на вопрос о факультете 
	if text not in cf.dist_personal_dict.keys() and text != cf.COMPLETE_CHOOSING:
		logger.info("Facility of %s, %s: %s", user.first_name, user.id, text)
		users_data.loc[user.id, 'Facility'] = text
	elif text != cf.COMPLETE_CHOOSING:
		logger.info("Dist of %s, %s: %s", user.first_name, user.id, text)
		if users_data.loc[user.id, text] == None:
			slot = None
			try:
				slot = cf.time_table_dict[text].booking_slot(rand = False,
															list_of_unavailable = users_data.loc[user.id, cf.users.RES_TIME ])
				
				users_data.loc[user.id, text] = slot[0]
				users_data.loc[user.id, cf.users.RES_TIME].append(slot[1:3])
				await update.message.reply_text(
				time.strftime("Ваше время старта на дистанции: %H:%M.\n", time.localtime(slot[1]))+
				"Пожалуйста, не опаздывайте;)"
				)

			except Exception as e:
				processing_exceptions(update.message, context, e)

		else:
			try:
				slot_num = users_data.loc[user.id, text]
				start_time = cf.time_table_dict[text].table[ slot_num ].start
				await update.message.reply_text(
					"Вы уже зарегистрированы на дистанцию "+ text + ".\n" +
					time.strftime("Старт в %H:%M.\n", time.localtime(start_time))
				
				)
			except Exception as e:
				processing_exceptions(update.message, context, e)

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
		cf.dist_group_keyboard, one_time_keyboard=True, input_field_placeholder="Выберете дистанции"
	),
	)
	return DIST

async def team_reg_dist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Starts the conversation and asks the user about distance."""

	user_id = update.message.from_user.id
	dist = update.message.text
	try:
		print(cf.teams.team_dict.index)
		cf.teams.team_dict.at[(user_id, dist), 'Tg_id_major'] = user_id
		cf.teams.team_dict.at[(user_id, dist), 'Distance'] = dist
	except Exception as e:
		print(e.args)

	await update.message.reply_text(
	   "Как будет называться команда?\n"
	)
	return NAME

#служебная функция для обнаружения названия дистанции
async def find_dist_name(user_id) -> str:
	dist_name = None
	for try_dist_name in cf.dist_group_dict.keys:
		if [user_id, try_dist_name] in cf.teasm.teams_dict.index:
			dist_name = try_dist_name
			break
	else:
		raise Exception("team_reg_name: Can not find index in dist_group_dict")
	# Если ничего не нашли он остался None
	return dist_name

async def team_reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Asks the user about team name."""

	user_id = update.message.from_user.id
	dist = find_dist_name(user_id)

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

#служебная функция для обнаружения номера ещё пустого пользователя
async def find_first_empty_member(user_id, dist_name) -> int:
	member_num = None
	for num in range(1,4):
		if cf.teasm.teams_dict.loc[[user_id, dist_name],'Member_id_' + str(num) ] == pd.non:
			member_num = num
			break
	else:
		raise Exception("find_first_empty_member: Can not find empty member in dist_group_dict")
	# Если ничего не нашли он остался None
	return member_num

async def team_reg_add_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Asks the user about team name."""

	user_id = update.message.from_user.id
	dist = find_dist_name(user_id)
	new_member_id = update.message.text

	# Проверка, есть ли такой id в зарегистрированных
	if new_member_id not in cf.users.user_dict.index:
		await update.message.reply_text(
			"Я не знаком с таким человеком( Он точно регистрировался у меня?\n"
			"Если у вашего знакомого нет Телеграмм, то попросите главного судью любой дистанции - они вам помогут."
			)
		return MEMBERS_ADD

	# Обработка id, если он найден
	else:
		new_member_num = find_first_empty_member(user_id, dist)
		num_of_remaining_members = cf.dist_group_team_members_count[dist] - 1 - new_member_num

		# Записали id всех участников
		if num_of_remaining_members == 0:
			await update.message.reply_text(
			"Команда " + cf.teams.team_dict.loc[(user_id, dist), 'Name'] + " зарегистрирована.\n"
			"Участникам отправлены запросы на подтверждение. Как только я получу все подтверждения, сразу извещу вас."
			"Время старта пришлю тогда же"
			)
			# Отправляем запросы на подтверждение
			major_name = cf.users.user_dict.loc[major_id, 'Name']
			members_list = None
			for member_num in range(1, cf.dist_group_team_members_count[dist]):
				member_id = cf.teams.team_dict.loc[(user_id, dist), 'Member_id_' + member_num]
				member_name = cf.users.user_dict.loc[member_id, 'Name']
				members_list += member_name + "\n"
			members_list = major_name + "  - Зарегистрировал команду\n" + members_list

			for member_num in range(1, cf.dist_group_team_members_count[dist]):
				member_id = cf.teams.team_dict.loc[(user_id, dist), 'Member_id_' + member_num]
				major_id = cf.teams.team_dict.loc[(user_id, dist), 'Tg_id_major' ]

				# не знаю, насколько это красиво, но тогда по нажатию на кнопку я получу всю информацию.
				keyboard = [
						[
						    InlineKeyboardButton("Согласен", callback_data= str(major_id) + "|" + dist + "Y"),
						    InlineKeyboardButton("Не согласен", callback_data= str(major_id) + "|" + dist + "N"),
						] ]
				reply_markup = InlineKeyboardMarkup(keyboard)

				await context.bot.send_message( chat_id= member_id,
					text  = 
					"Вы согласны участвовать в команде " + cf.teams.team_dict.loc[(user_id, dist), 'Name'] + ",\n"
					"На дистанции " + cf.teams.team_dict.loc[(user_id, dist), 'Distance'] + ",\n"
					"В составе:" + members_list + "?",
					reply_markup= reply_markup
					)
			return CONFIRM

		# Ещё не все участники записаны
		else:
			cf.teams.team_dict.loc[(user_id, dist), 'Member_id_' + str(new_member_num)] = new_member_id
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

	major_id = data[0 : id_size]
	dist = data[id_size + 1 : -1]
	mean = data[-1]

	major_name = cf.users.user_dict.loc[major_id, 'Name']
	members_list = None
	for member_num in range(1, cf.dist_group_team_members_count[dist]):
		member_id = cf.teams.team_dict.loc[(user_id, dist), 'Member_id_' + member_num]
		member_name = cf.users.user_dict.loc[member_id, 'Name']
		members_list += member_name + "\n"
	members_list = major_name + "  - Зарегистрировал команду\n" + members_list

	if mean == "Y":
		cf.teams.team_dict.loc[(user_id, dist),'Member_comfurm_num'] += 1
		await query.edit_message_text(text="Спасибо! Как только я получу все подтверждения, то сразу подберу вам время старта.")

		# Назначаем время старта
		if cf.teams.team_dict.loc[(user_id, dist),'Member_comfurm_num'] == dist_group_team_members_count[dist]:
			unawalable_list = None
			# Собираем список занятых времён
			for member_column in cf.teams.team_dict[['Member_id_1', 'Member_id_2','Member_id_3','Member_id_4']]:
				member_id = cf.teams.team_dict.loc[(user_id, dist), member_column]
				member_unw_list = cf.users.user_dict.loc[member_id, cf.Users.RES_TIME]
				unawalable_list.append(member_unw_list)
			
			# Выбираем слот
			try:
				slot = cf.time_table_dict[text].booking_slot(rand = False,
															list_of_unavailable = unawalable_list)
			except Exseption as ex:
				processing_exceptions(update.message, context, e)


			# Назначаем слот команде
			cf.teams.team_dict.loc[(user_id, dist), 'Slot_num'] = slot[0]
			# Добавляем время нахождения на дистанции к занятому времени у всех участников.
			for member_column in cf.teams.team_dict[['Member_id_1', 'Member_id_2','Member_id_3','Member_id_4']]:
				member_id = cf.teams.team_dict.loc[(user_id, dist), member_column]
				cf.users.user_dict.loc[member_id, cf.Users.RES_TIME].append(slot[0:2])
		
		return ConversationHandler.END


	else:
		#Оповещаем всех об отмене, сбрасываем команду.
		
		for member_column in cf.teams.team_dict[['Member_id_1', 'Member_id_2','Member_id_3','Member_id_4']]:
			member_id = cf.teams.team_dict.loc[(user_id, dist), member_column]
			await context.bot.send_message( chat_id= member_id,
				text  = 
				"Кто-то не соглачен участвовать в команде " + cf.teams.team_dict.loc[(user_id, dist), 'Name'] + ",\n"
				"На дистанции " + cf.teams.team_dict.loc[(user_id, dist), 'Distance'] + ",\n"
				"В составе:" + members_list + ".\n"
				"Я вынужден отменить регистрацию команды."
				)

		major_id = cf.teams.team_dict.loc[(user_id, dist), 'Tg_id_major' ]
		await context.bot.send_message( chat_id= member_id,
			text  = 
			"Кто-то не соглачен участвовать в команде " + cf.teams.team_dict.loc[(user_id, dist), 'Name'] + ",\n"
			"На дистанции " + cf.teams.team_dict.loc[(user_id, dist), 'Distance'] + ",\n"
			"В составе:" + members_list + ".\n"
			"Я вынужден отменить регистрацию команды.")

		cf.teams.team_dict.loc[(user_id, dist)].clean()

		return ConversationHandler.END
