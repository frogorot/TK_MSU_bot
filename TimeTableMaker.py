
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

import interface
import core_funcs as cf


def main() -> None:



	""" Configure interface."""
	""" Load conf files."""
	run_file = "run.ini"
	run_pars = cf.Parser()
	run_pars.load_toml(run_file)

	sucere_pars = cf.Parser()
	sucere_pars.load_toml(run_pars.at('secure_file'))
	info_pars = cf.Parser()
	info_pars.load_toml(run_pars.at('info_file'))
	secure_directory = run_pars.at('secure_dir')
	info_directory = run_pars.at('info_dir')

	""" Load data."""
	""" Load distance data."""
	pers_dist_group_name = 'personal_distances'
	group_dist_group_name = 'group_distances'
	open_time_str = "open_time" # часы:минуты
	close_time_str = "close_time" # часы:минуты
	interval_str = "interval" # минуты:секунды
	passing_time_str = "passing_time" # минуты:секунды

	for p_dist in info_pars.at(pers_dist_group_name):
		name = info_pars.at(pers_dist_group_name)[p_dist]
		cf.dist_personal_dict[name] = cf.DistanceResults(name)
		dist_params = info_pars.at(p_dist) 

		open_time = int(dist_params[open_time_str][0:2]) * 3600 + int(dist_params[open_time_str][3:5]) * 60
		close_time = int(dist_params[close_time_str][0:2]) * 3600 + int(dist_params[close_time_str][3:5]) * 60
		interval = int(dist_params[interval_str][0:2]) * 60 + int(dist_params[interval_str][3:5])
		passing_time = int(dist_params[passing_time_str][0:2]) * 60 + int(dist_params[passing_time_str][3:5])
		#minutes=int(dist_params[open_time_str][3:4]), hours= int(dist_params[open_time_str][0:1]))
		#open_time = datetime(year=2022, month=10, day=15, hour= int(dist_params[open_time_str][0:1]), minute= int(dist_params[open_time_str][3:4]), second = 0)
		#close_time = datetime(year=2022, month=10, day=15, hour= int(dist_params[close_time_str][0:1]), minute= int(dist_params[close_time_str][3:4]), second = 0)
		#interval = datetime(year=2022, month=10, day=15, hour= 0, minute= int(dist_params[open_time_str][0:1]), second = int(dist_params[passing_time_str][3:4]))
		#passing_time = datetime(year=2022, month=10, day=15, hour= 0, minute= int(dist_params[open_time_str][0:1]), second = int(dist_params[passing_time_str][3:4]))

		cf.time_table_dict[name] = cf.TimeTable(name, 
												open_time= open_time,
												close_time= close_time,
												interval= interval,
												passing_time= passing_time)
	for g_dist in info_pars.at(group_dist_group_name):
		name = info_pars.at(group_dist_group_name)[g_dist]
		cf.dist_group_dict[name] = cf.DistanceResults(name)

		open_time = int(dist_params[open_time_str][0:2]) * 3600 + int(dist_params[open_time_str][3:5]) * 60
		close_time = int(dist_params[close_time_str][0:2]) * 3600 + int(dist_params[close_time_str][3:5]) * 60
		interval = int(dist_params[interval_str][0:2]) * 60 + int(dist_params[interval_str][3:5])
		passing_time = int(dist_params[passing_time_str][0:2]) * 60 + int(dist_params[passing_time_str][3:5])

		cf.time_table_dict[name] = cf.TimeTable(name, 
												open_time= open_time,
												close_time= close_time,
												interval= interval,
												passing_time= passing_time)


	API_TOKEN =  sucere_pars.at('Token')

	"""Run the interface."""
	# Create the Application and pass it your interface's token.
	application = Application.builder().token(API_TOKEN).build()

	# Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("start", interface.user_reg_start)],
		states={
			interface.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, interface.user_reg_age)],
			interface.GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, interface.user_reg_gender)],
			interface.UNIVERSITY: [MessageHandler(filters.Regex("^(Мальчик|Девочка)$"), interface.user_reg_university)],
			interface.FACILITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, interface.user_reg_facility)],
			interface.DISTANCES: [MessageHandler(filters.Regex("^(Горная|Пешеходная|Водная|Вело|Охота на лис)$"), interface.user_reg_distances)],
		},
		fallbacks=[CommandHandler("cancel", interface.cancel)],
	)

	application.add_handler(conv_handler)
	print("Bot start")

	# Run the interface until the user presses Ctrl-C
	application.run_polling()
  

if __name__ == "__main__":
	main()