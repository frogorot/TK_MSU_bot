
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

import user_interface
import core_funcs as cf
from  core_funcs import Containers as Cont


def main() -> None:



	""" Configure interface."""
	""" Load conf files."""
	run_file = "run.ini"
	loader = cf.Loader(run_file)

	#run_file = "run.ini"
	#run_pars = cf.Parser()
	#run_pars.load_toml(run_file)
	#
	#sucere_pars = cf.Parser()
	#sucere_pars.load_toml(run_pars.at('secure_file'))
	#info_pars = cf.Parser()
	#info_pars.load_toml(run_pars.at('info_file'))
	#secure_directory = run_pars.at('secure_dir')
	#info_directory = run_pars.at('info_dir')

	""" Load data."""
	""" Load distance data."""
	loader.load()

	#pers_dist_group_name = 'personal_distances'
	#group_dist_group_name = 'group_distances'
	#open_time_str = "open_time" # часы:минуты
	#close_time_str = "close_time" # часы:минуты
	#interval_str = "interval" # минуты:секунды
	#passing_time_str = "passing_time" # минуты:секунды

	#NUM_OF_KEYS_IN_ROW_FOR_DIST = 3
	#i = 0
	#row = []
	#
	#for p_dist in info_pars.at(pers_dist_group_name):
	#	name = info_pars.at(pers_dist_group_name)[p_dist]
	#	cf.dist_personal_dict[name] = cf.DistanceResults(name)
	#	cf.Users.list_of_params.append(name)
	#
	#	dist_params = info_pars.at(p_dist) 
	#
	#	open_time = int(dist_params[open_time_str][0:2]) * 3600 + int(dist_params[open_time_str][3:5]) * 60
	#	close_time = int(dist_params[close_time_str][0:2]) * 3600 + int(dist_params[close_time_str][3:5]) * 60
	#	interval = int(dist_params[interval_str][0:2]) * 60 + int(dist_params[interval_str][3:5])
	#	passing_time = int(dist_params[passing_time_str][0:2]) * 60 + int(dist_params[passing_time_str][3:5])
	#	#minutes=int(dist_params[open_time_str][3:4]), hours= int(dist_params[open_time_str][0:1]))
	#	#open_time = datetime(year=2022, month=10, day=15, hour= int(dist_params[open_time_str][0:1]), minute= int(dist_params[open_time_str][3:4]), second = 0)
	#	#close_time = datetime(year=2022, month=10, day=15, hour= int(dist_params[close_time_str][0:1]), minute= int(dist_params[close_time_str][3:4]), second = 0)
	#	#interval = datetime(year=2022, month=10, day=15, hour= 0, minute= int(dist_params[open_time_str][0:1]), second = int(dist_params[pauser_interfacessing_time_str][3:4]))
	#	#passing_time = datetime(year=2022, month=10, day=15, hour= 0, minute= int(dist_params[open_time_str][0:1]), second = int(dist_params[passing_time_str][3:4]))
	#	
	#	#Генерим пустой стартовый протокол.
	#	cf.time_table_dict[name] = cf.TimeTable(name, 
	#											open_time= open_time,
	#											close_time= close_time,
	#											interval= interval,
	#											passing_time= passing_time)
	#	#Генерим клавиатуру
	#	if i == NUM_OF_KEYS_IN_ROW_FOR_DIST:
	#		cf.dist_personal_keyboard.append(row)
	#		row = []
	#		i -= NUM_OF_KEYS_IN_ROW_FOR_DIST
	#	i += 1
	#	row.append(name)
	#
	#cf.dist_personal_keyboard.append(row)
	#cf.dist_personal_keyboard.append([ cf.COMPLETE_CHOOSING])
	#row = []
	#i = 0
	#
	#for g_dist in info_pars.at(group_dist_group_name):
	#	name = info_pars.at(group_dist_group_name)[g_dist]
	#	cf.dist_group_dict[name] = cf.DistanceResults(name)
	#
	#	open_time = int(dist_params[open_time_str][0:2]) * 3600 + int(dist_params[open_time_str][3:5]) * 60
	#	close_time = int(dist_params[close_time_str][0:2]) * 3600 + int(dist_params[close_time_str][3:5]) * 60
	#	interval = int(dist_params[interval_str][0:2]) * 60 + int(dist_params[interval_str][3:5])
	#	passing_time = int(dist_params[passing_time_str][0:2]) * 60 + int(dist_params[passing_time_str][3:5])
	#	
	#	#Генерим пустой стартовый протокол.
	#	cf.time_table_dict[name] = cf.TimeTable(name, 
	#											open_time= open_time,
	#											close_time= close_time,
	#											interval= interval,
	#											passing_time= passing_time)
	#	#Генерим клавиатуру
	#	if i == NUM_OF_KEYS_IN_ROW_FOR_DIST:
	#		cf.dist_group_keyboard.append(row)
	#		row = []
	#		i -= NUM_OF_KEYS_IN_ROW_FOR_DIST
	#	i += 1
	#	row.append(name)
	#cf.dist_group_keyboard.append(row)
	#cf.dist_group_keyboard.append([ cf.COMPLETE_CHOOSING])

	#API_TOKEN =  sucere_pars.at('Token')
	#cf.admin_chat_id = sucere_pars.at('admin_chat_id')

	"""Run the interface."""
	# Create the Application and pass it your interface's token.
	application = Application.builder().token(Cont.api_token).build()

	#/Help handler
	help_hendler = CommandHandler("help", user_interface.send_welcome)

	#/ask_admin handler
	admin_connect_handler = ConversationHandler(
		entry_points=[CommandHandler("ask_admin", user_interface.process_ask_admin)],
		states={
			user_interface.MESSAGE_TO_ADMIN: [MessageHandler(filters.ALL, user_interface.process_send_to_admin)],
			#user_interface.MESSAGE_TO_ADMIN: [MessageHandler(~filters.TEXT, user_interface.process_send_to_admin)],
		},
		fallbacks=[CommandHandler("cancel", user_interface.cancel)],
	)

	#/user Handler
	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("start", user_interface.user_reg_start)],
		states={
			user_interface.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_age)],
			user_interface.GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_gender)],
			user_interface.UNIVERSITY: [MessageHandler(filters.Regex("^(Мальчик|Девочка)$"), user_interface.user_reg_university)],
			user_interface.FACILITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_facility)],
			user_interface.DISTANCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_distances)],
		},
		fallbacks=[CommandHandler("cancel", user_interface.cancel),
			 MessageHandler(filters.Regex("^(" + Cont.COMPLETE_CHOOSING + ")$"), user_interface.user_reg_distances)],
	)

	application.add_handler(help_hendler)
	application.add_handler(admin_connect_handler)
	application.add_handler(conv_handler)
	print("Bot start")

	# Run the interface until the user presses Ctrl-C
	application.run_polling()


if __name__ == "__main__":
	main()