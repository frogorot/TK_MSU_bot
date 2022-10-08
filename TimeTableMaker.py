
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
import judge_interface

import core_funcs as cf


def main() -> None:

	""" Configure interface."""
	""" Load conf files."""
	run_file = "run.ini"
	#API_TOKEN =  secure_pars.at('Token')
	#cf.admin_chat_id = secure_pars.at('admin_chat_id')
	loader = cf.Loader(run_file)

	""" Load data."""
	loader.load()

	"""Run the interface."""
	# Create the Application and pass it your interface's token.
	application = Application.builder().token(cf.api_token).build()

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
			 MessageHandler(filters.Regex("^(" + cf.COMPLETE_CHOOSING + ")$"), user_interface.user_reg_distances)],
	)
	# /judge Handler
	judge_interface.notify
	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("start", judge_interface.judge_reg_start)],
		states={
			judge_interface.DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, judge_interface.judge_reg_distance)]
		},
		fallbacks=[CommandHandler("cancel", judge_interface.cancel)],
	)

	application.add_handler(help_hendler)
	application.add_handler(admin_connect_handler)
	application.add_handler(conv_handler)
	print("Bot start")

	# Run the interface until the user presses Ctrl-C
	application.run_polling()


if __name__ == "__main__":
	main()