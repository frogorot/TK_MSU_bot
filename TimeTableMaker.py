import re

#from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
	Application,
	CommandHandler,
	#ContextTypes,
	ConversationHandler,
	MessageHandler,
	CallbackQueryHandler,
	filters,
)
import core_funcs as cf

import user_interface
import judge_interface

def main() -> None:

	""" Configure interface."""
	""" Load conf files."""
	run_file = "run.ini"

	loader = cf.Loader(run_file)

	""" Load data."""
	loader.load()

	"""Run the interface."""
	# Create the Application and pass it your interface's token.
	application = Application.builder().token(cf.api_token).build()
	
	# Настройка сохранений
	job_queue = application.job_queue

	job_write_all = job_queue.run_repeating(
		cf.write_all_data, 
		interval=600, first=600, # Сохраняем раз в 10 минут
		name = user_interface.WRITE_ALL_DATA_JOB
		)
	user_interface.job_dict[job_write_all.name] = job_write_all

	###########################################
	#Admin commands
	#/forced_load handler
	forced_load_hendler = CommandHandler("forced_load", 
									  filters = filters.User(user_id = cf.admin_chat_id), 
										callback= user_interface.admin_forced_load)
	#/forced_write handler
	forced_write_hendler = CommandHandler("forced_write", 
									  filters = filters.User(user_id = cf.admin_chat_id), 
										callback= user_interface.admin_forced_write)
	#/stop_writes handler
	stop_writes_hendler = CommandHandler("stop_writes", 
									  filters = filters.User(user_id = cf.admin_chat_id), 
										callback= user_interface.admin_stop_writes)
	#/start_writes handler
	start_writes_hendler = CommandHandler("start_writes", 
									  filters = filters.User(user_id = cf.admin_chat_id), 
										callback= user_interface.admin_start_writes)
	#/get_all_data handler
	send_all_data_hendler = CommandHandler("get_all_data", 
									  filters = filters.User(user_id = cf.admin_chat_id), 
										callback= user_interface.admin_send_all_data)

	#Addind admin command hendlers
	application.add_handlers(handlers = [
		forced_load_hendler, 
		forced_write_hendler, 
		stop_writes_hendler, 
		start_writes_hendler,
		send_all_data_hendler])


	###########################################
	#User commands
	#
	#/Help handler
	help_hendler = CommandHandler("help", user_interface.send_welcome)

	#/my_dist handler
	my_dist_handler = CommandHandler("my_dist", user_interface.user_print_dist)
	#/new_dist Handle
	new_dist_hendler = CommandHandler("new_dist", user_interface.user_new_dist)

	#/ask_admin handler
	admin_connect_handler = ConversationHandler(
		entry_points=[CommandHandler("ask_admin", user_interface.process_ask_admin)],
		states={
			user_interface.MESSAGE_TO_ADMIN: [MessageHandler(filters.ALL, user_interface.process_send_to_admin)],
			#user_interface.MESSAGE_TO_ADMIN: [MessageHandler(~filters.TEXT, user_interface.process_send_to_admin)],
		},
		fallbacks=[CommandHandler("cancel", user_interface.cancel)],
	)

	#/start Handler
	user_reg_handler = ConversationHandler(
		entry_points=[CommandHandler("start", user_interface.user_reg_start)],
		states={
			user_interface.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_age)], #функция возвращает состояние AGE, есть лист обработчиков,
			user_interface.GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_gender)],
			user_interface.UNIVERSITY: [MessageHandler(filters.Regex("^(Мальчик|Девочка)$"), user_interface.user_reg_university)],
			user_interface.FACILITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_facility)],
			user_interface.DISTANCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_distances)],
		},
		fallbacks=[CommandHandler("cancel", user_interface.cancel),
			 MessageHandler(filters.Regex("^(" + cf.COMPLETE_CHOOSING + ")$"), user_interface.user_reg_distances)],
	)

	#/new_team Handler
	team_reg_handler = ConversationHandler(
		entry_points=[CommandHandler("new_team", user_interface.team_reg_start)],
		states={
			user_interface.DIST: [MessageHandler(filters.Regex(cf.re_str_group_disr), user_interface.team_reg_dist)],
			user_interface.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.team_reg_name)],
			user_interface.MEMBERS_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.team_reg_add_member)],
			user_interface.CONFIRM: [CallbackQueryHandler(user_interface.team_reg_confirm)],
		},
		fallbacks=[CommandHandler("cancel", user_interface.cancel) ]#,
			# MessageHandler(filters.Regex("^(" + cf.COMPLETE_CHOOSING + ")$"), user_interface.user_reg_distances)],
	)

	#Confirm to be member of team Handler
	pattern_for_tem_reg_confirm = re.compile(cf.TEAM_REG_PREFIX)
	team_reg_confirm = CallbackQueryHandler(user_interface.team_reg_confirm, pattern= pattern_for_tem_reg_confirm)

	application.add_handlers( handlers = [
		help_hendler,
		my_dist_handler,
		admin_connect_handler, 
		user_reg_handler, 
		team_reg_handler, 
		team_reg_confirm])

	###########################################
	#Judge commands
	#
	# /judge Handler
	#judge_reg_handler = ConversationHandler(
	#	entry_points=[CommandHandler("admin_judge_start", judge_interface.notify, filters = filters.User(user_id = cf.admin_chat_id))],
	#	states={
	#		judge_interface.DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, judge_interface.judge_reg_start)]
	#		#judge_interface.DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, judge_interface.judge_reg_distance)]
	#	},
	#	fallbacks=[CommandHandler("cancel", judge_interface.cancel)],
	#)
	#
	#application.add_handler(judge_reg_handler)
	print("Bot start")

	# Run the interface until the user presses Ctrl-C
	application.run_polling()


if __name__ == "__main__":
	main()