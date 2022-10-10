
admin_chat_id = {}

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

import user_interface
import core_funcs as cf


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
	user_reg_handler = ConversationHandler(
		entry_points=[CommandHandler("start", user_interface.user_reg_start)],
		states={
			user_interface.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_age)],
			user_interface.GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_gender)],
			user_interface.UNIVERSITY: [MessageHandler(filters.Regex("^(Мальчик|Девочка)$"), user_interface.user_reg_university)],
			user_interface.FACILITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_interface.user_reg_facility)],
			user_interface.DISTANCES: [MessageHandler(filters.Regex(cf.re_str_pesr_disr), user_interface.user_reg_distances)],
		},
		fallbacks=[CommandHandler("cancel", user_interface.cancel),
			 MessageHandler(filters.Regex("^(" + cf.COMPLETE_CHOOSING + ")$"), user_interface.user_reg_distances)],
	)

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


	application.add_handler(help_hendler)
	application.add_handler(admin_connect_handler)
	application.add_handler(user_reg_handler)
	application.add_handler(team_reg_handler)
	print("Bot start")

	# Run the interface until the user presses Ctrl-C
	application.run_polling()


if __name__ == "__main__":
	main()