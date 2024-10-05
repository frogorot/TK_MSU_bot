import random
import toml
import pandas as pd
import re
#import pathlib 
import time
from datetime import datetime
from os import path

#SECURE_DIRECTORY_NAME = 'secure_info'
#INFO_DIRECTORY_NAME = 'load_info'
#SHEETS_DIRECTORY_NAME = 'sheets'
SHEET_EXTENTION = '.xlsx'
AUTENTIFICATION_EXTENTION = '.aut'
ARCHIVE_PATH = 'Archive/'

COMPLETE_CHOOSING = 'Завершить'

TEAM_REG_PREFIX = "TEAM_REG_"

TEAM_NAME_LENTH = 50

#class Containers:
secure_directory = None
info_directory = None

time_table_dict = {}

dist_personal_dict = {}
dist_personal_keyboard = []
re_str_pesr_disr = None


stages_mountain_simple_keyboard = []
stages_mountain_complex_keyboard = []
stages_fox_hunting_keyboard = []
stages_adventure_keyboard = []
stages_water_katamaran_keyboard = []
stages_bike_keyboard = []
stages_pedestrian_keyboard = []


users = None
judges = None
teams = None

api_token = None
admin_chat_id = None



# идеи
# slot - это строка(пустая или непустая) в стартовом протоколе
class Parser:
	def __init__(self):
		self.parsed_toml = None

	def load_toml(self, ini_file: str):
		""" ini_file shoud be a full name"""
		#path = pathlib.Path(ini_file)
		#str_path = str(path)
		#print(ini_file)

		self.parsed_toml = toml.load(ini_file)

	def at(self, atribute: str):
		"""Returns value of "atribute" from "ini_file"."""
		if self.parsed_toml != None and atribute in self.parsed_toml.keys():
			return self.parsed_toml[atribute]
		else: 
			return None


#def is_seg_nin_seg_list(moment: (int, int), segment_list: list(int, int))-> bool: 
#	# Проверяет, находится пересекается ли отрезок с каким-то отрезком из списка
#
#	for segment in segment_list:
#		if moment(1) >= segment[0] and moment(0) <= segment[1]: # Проще всего проверить истинность, если взять отрицание
#			return False
#	else:
#		return True


def is_seg_nin_seg_list(left_point: int, length: int, segment_list: list)-> bool: 
	# Проверяет, находится пересекается ли отрезок, заданный лывой точкой и длинной, с каким-то отрезком из списка
	right_point = left_point + length
	for segment in segment_list: # Совсем по хорошему надо насовать проверок, но лень.
		if left_point <= segment[1] and right_point >= segment[0]: # Проще всего проверить истинность, если взять отрицание
			return False
	else:
		return True

def gene_table(open_time: int, close_time: int, interval: int):
	i = open_time
	while i <= (close_time - interval):
		yield i
		i += interval
# open_time - время открытия дистанции, close_time - время закрытия дистанции
def from_start_time_to_num_default(current_start_time, open_time, interval): #конверитирует время старта слота в его номер
	return int((current_start_time - open_time) / interval)

class Distance:
	# open_time - время открытия дистанции, close_time - время закрытия дистанции
	ON_A_FIRST_COME = "time_now"
	WINDOW_WIDTH = 6

	dist_param_list = ["time",		# время старта
					"user_id"]	# Id участника или команды.

	def __init__(self, distance: str, open_time: int, close_time: int, interval: int, passing_time: int):
		self.name = distance

		self.table = pd.DataFrame(columns = Distance.dist_param_list) 

		self.table_of_free = self.table[self.table["user_id"] == None]["time"] # Series, которая хранит только свободные времена. 
		self.table[Distance.ON_A_FIRST_COME, []] # Добавляем особое время - по живой очереди.

	# 
	def updateFree(self, current_time: int):
		self.table_of_free = self.table[self.table["user_id"] == None]["time"] # Взяли из столбца только свободные времена.
		# вроде так сохранятся родны индексы, так что по ним и будем гулять.
		if current_time != None: # Выкинули прошедшие времена старта.
			self.table_of_free = self.table_of_free[self.table_of_free["time"] > current_time] 
		self.table_of_free.sort_values()
	
	# по желаемому времени находит window ближайших свободных. 
	# Возвращает список из не более чем window ближайших пар (индекс, время)
	def findNearFree(self, desiredTime, window: int = WINDOW_WIDTH) -> List: 
		
		if self.table_of_free.empty() :
			return []

		pos = self.table_of_free.searchsorted(dsiredTime)
		free_list = [ (pos,self.table_of_free.at[pos]) ]
		start = pos - window/2 - 1
		finish = pos + window/2

		# сдвигаем всё окно в положительную область.
		if start < 0:
			finish = finish - start 
			start = 0
		
		# Если окно выпало справа, то сдвигаем его влево, возможно, сжимая.
		fshift = finish - len(self.table_of_free) + 1
		if fshift > 0 :
			if start > fshift :
				start = start - fshift
			else : 
				start = 0

			finish = len(self.table_of_free) - 1

		while start < finish :
			free_list.append( (start, self.table_of_free.at[start]) )
			start +=1

		return free_list

	# Пытается записать userId на время slot[1] в позиции slot[0]. Проверяет, что slot есть в  table_of_free и table, а так же, что он свободен.
	def bookingSlot(self, slot : (int, time), userId ) -> bool:
		
		if self.table_of_free.at(slot[0]) != slot[1]:
			return False

		if self.table.at[slot[0]]["time"] != slot[1] :
			raise Exception('Distance::booking_slot - slot ' + slot[0] + ' at ' + slot[1] + ' not in Tadle. Use updateFree')
			return False

		if self.table.at[slot[0]]["user_id"] != None :
			raise Exception('Distance::booking_slot - slot ' + slot[0] + ' at ' + slot[1] + ' not free.')
			self.table_of_free.pop(slot[0])
			return False

		self.table.at[slot[0]]["user_id"] = userId
		self.table_of_free.pop(slot[0])
		return True
	
	# ON_A_FIRST_COME всегда лежит в 0.
	def addToFirstCome(self, userId) :
		self.table.at[0, "user_id"].append(userId)

	def free_slots(self):
		return table_of_free

	def getTable(self):
		return self.table

	def getUsers(self):
		return self.table["user_id"]
	
	def retun_filename(self) -> str:
		return info_directory + self.name + SHEET_EXTENTION

	# Обновляет таблицу путём перезаписи. То есть старая удаляется, новая сохраняется.
	# Возвращает три списка пар (userId, time), со всеми теми userId, которые имеют разные времена в старом и новом расписании. В том числе, удалённые из какого-то
	def setTable(self, new_table: pd.DataFrame) -> Typle:

		old_users = self.table["user_id"]
		new_users = new_table["user_id"]

		renewList = ( new_row for row, new_row in zip(self.table.itertuples(), new_table.itertuples())  if row["user_id"] == new_row["user_id"] and row["time"] != new_row["time"])
		addList = ( new_row for new_row in new_table.itertuples()  if not old_users.isin(new_row["user_id"]).all() )	 
		deleteList = ( row for row in self.table.itertuples()  if not new_users.isin(row["user_id"]).all() )

		self.table = new_table

		return (renewList,  addList, deleteList)

	def write_TT(self, filename: str = ""):

		time_str = time.strftime("-%m.%d.%Y_%H-%M-%S", time.localtime(time.time()))

		write_file_name = ""
		if filename == "":
			write_file_name += self.name
		else:
			write_file_name += filename

		self.table.to_excel(info_directory + ARCHIVE_PATH + write_file_name +  time_str + SHEET_EXTENTION)
		self.table.to_excel(info_directory + write_file_name + SHEET_EXTENTION)

	def load_TT(self, filename: str = "") -> Typle:
		load_file_path = info_directory

		renewTyple = ()

		if filename == "":
			load_file_path += self.name + SHEET_EXTENTION
		else:
			load_file_path += filename + SHEET_EXTENTION

		if path.isfile(load_file_path):
			load_df = pd.read_excel(load_file_path)
			
			if load_df[0, "time"] != ON_A_FIRST_COME :
				raise Exception("Distance::load_TT: Wrong data in filename=" + load_file_path + ". There is no " + ON_A_FIRST_COME + " in first row.")
			else: 
				if not set(Distance.dist_param_list).issubset(self.user_dict.columns):
					raise Exception("Distance::load_TT: Wrong data in filename=" + load_file_path + ". There is no Distance::dist_param_list.")
				else:
					renewTyple = self.setTable(load_df)
		else:
			print("There is no " + load_file_path + "\n")

		return renewTyple
	

class Users:
	MALE, FEMALE = range(2)

	list_of_params = ['Tg_id', 
						  'Name', 
						  'Age', 
						  'Sex', 
						  'University', 
						  'Facility']

	def __init__(self, dist_dict):
		self.filename = "Users"

		list_of_params = list_of_params + dist_dict # Каждая дистанция просто даёт отдельный столбец. В ячейки пустота или номер слота.
		self.user_dict = pd.DataFrame(columns = Users.list_of_params) #Дистанции - список, этапы - словарь = {дистанция:этап}
		self.user_dict = self.user_dict.set_index('Tg_id')

	def retunFilename(self) -> str:
		write_file_name = ""
		if self.filename == "":
			write_file_name += "Users"
		else:
			write_file_name += self.filename
		return info_directory + write_file_name + SHEET_EXTENTION

	def writeUsers(self):
		if self.filename == None:
			self.filename = "Users"

		time_str = time.strftime("-%m.%d.%Y_%H-%M-%S", time.localtime(time.time()))

		self.user_dict.to_excel(info_directory + ARCHIVE_PATH + self.filename + time_str + SHEET_EXTENTION)
		self.user_dict.to_excel(info_directory + self.filename + SHEET_EXTENTION)

	def loadUsers(self, filename: str = "Users"):
		if filename != None:
			self.filename = filename
		else:
			if self.filename == None:
				raise Exception("Users::load_users: empty file name and empty self.filename. I can't contine load")
		
		load_file_path = info_directory + self.filename + SHEET_EXTENTION
		if path.isfile(load_file_path):
			try:
				self.user_dict = pd.read_excel(load_file_path)

				if not set(Users.list_of_params).issubset(self.user_dict.columns): #проверка что нам дали адекватный файл(например не файл с судьями)
					self.user_dict = pd.DataFrame(columns = Users.list_of_params) #Дистанции - список, этамы - словарь = {дистанция:этап}
					raise Exception("Users::load_users: Wrong data in filename=" + filename + ". There is no Users::list_of_params.")
				# Устанавливаем индекс Tg_id. Если это сделать раньше, то проапдёт соответствующая колонка и не красиво проверять
				self.user_dict = self.user_dict.set_index('Tg_id')

				# Список слотов конкретного пользоывателя получаем автоматически. Ничего парсить не надо.
			except Exception as e:
				print(e.args)
		else:
			print("There is no " + load_file_path + "\n")

	def getUserData(self, userId, data_name: str) :
		return self.user_dict.at[userId, data_name]

	def setUserData(self, userId, data_name: str, data) :
		self.user_dict.at[userId, data_name] = data


from telegram.ext import ContextTypes

#запись всех данных
async def write_all_data(context: ContextTypes.DEFAULT_TYPE):
	try:
		#Мы верим, что груповые и пешеходыне дистанции не пересекаются
		for dist_name in dist_personal_dict:
			dist_personal_dict[dist_name].write_protocol()
			time_table_dict[dist_name].write_TT(dist_name)

		for dist_name in dist_group_dict:
			dist_group_dict[dist_name].write_protocol()
			time_table_dict[dist_name].write_TT(dist_name)
		
		users.write_users()
		judges.write_aut_info()
		judges.write_judge_list()
		teams.write_teams()
	except Exception as e:
		print(e.args)

async def load_all_data():
	try:
		#Мы верим, что груповые и пешеходыне дистанции не пересекаются
		for dist_name in dist_personal_dict:
			dist_personal_dict[dist_name].load_protocol(dist_name)

			time_table_dict[dist_name].load_TT(dist_name)

		for dist_name in dist_group_dict:
			dist_group_dict[dist_name].load_protocol(dist_name)
			time_table_dict[dist_name].load_TT(dist_name)
		
		users.load_users()
		judges.load_aut_info()
		judges.load_judge_dict()
		teams.load_teams()
	except Exception as e:
		print(e.args)

class Loader:
	pers_dist_group_name = 'personal_distances'
	group_dist_group_name = 'group_distances'
	open_time_str = "open_time" # часы:минуты
	close_time_str = "close_time" # часы:минуты
	interval_str = "interval" # минуты:секунды
	passing_time_str = "passing_time" # минуты:секунды
	team_members_count = "team_members"

	NUM_OF_KEYS_IN_ROW_FOR_DIST = 3

	def __init__(self, run_name: str = "run.ini"):
		#run_file = "run.ini"
		self.run_pars = Parser()
		self.run_pars.load_toml(run_name)

	# Загрузка всего из conf файлов
	def load(self):
		# Объявляем global, а то эта собака считает, что переменные локальные. #"Я не собака, я питон!"
		global secure_directory
		global info_directory
		
		global time_table_dict
		
		global dist_personal_dict
		global dist_personal_keyboard
		global re_str_pesr_disr

		global dist_group_dict
		global dist_group_keyboard
		global dist_group_team_members_count
		global re_str_group_disr

		global stages_mountain_simple_keyboard
		global stages_mountain_complex_keyboard
		global stages_fox_hunting_keyboard
		global stages_adventure_keyboard
		global stages_water_katamaran_keyboard
		global stages_bike_keyboard
		global stages_pedestrian_keyboard

		global users
		global judges
		global teams
		
		global api_token
		global admin_chat_id


		# Загрузка парсеров
		self.sucere_pars = Parser()
		self.sucere_pars.load_toml(self.run_pars.at('secure_file')) #ключ 'secure_file',
		self.info_pars = Parser()
		self.info_pars.load_toml(self.run_pars.at('info_file'))
		secure_directory = self.run_pars.at('secure_dir')
		info_directory = self.run_pars.at('info_dir')
		# self.info_pars.at('mountain_simple') - получаю значения по этому ключу. self.info_pars.at('mountain_simple')['open_time']

		##############################################################
		#Загрузка секретной информации
		api_token = self.sucere_pars.at('Token')
		# делаем из словаря список
		admin_chat_id = [self.sucere_pars.at('admin_chat_id')[admin] for admin in self.sucere_pars.at('admin_chat_id') ]

		##############################################################
		re_str_pesr_disr = "^("
		re_str_group_disr = "^("

		# Служебные переменные
		row = []
		# Обработка информации по личным дистанциям
		for p_dist in self.info_pars.at(Loader.pers_dist_group_name):
			name = self.info_pars.at(Loader.pers_dist_group_name)[p_dist]
			dist_personal_dict[name] = DistanceResults(name)
			Users.list_of_params.append(name)

			# Создаём регулярку для распознования одного из названий дистанции
			if len(re_str_pesr_disr) > 2:
				re_str_pesr_disr += "|"
			re_str_pesr_disr += name

			dist_params = self.info_pars.at(p_dist) 

			open_time = int(dist_params[Loader.open_time_str][0:2]) * 3600 + int(dist_params[Loader.open_time_str][3:5]) * 60
			close_time = int(dist_params[Loader.close_time_str][0:2]) * 3600 + int(dist_params[Loader.close_time_str][3:5]) * 60
			interval = int(dist_params[Loader.interval_str][0:2]) * 60 + int(dist_params[Loader.interval_str][3:5])
			passing_time = int(dist_params[Loader.passing_time_str][0:2]) * 60 + int(dist_params[Loader.passing_time_str][3:5])
			
			#Генерим пустой стартовый протокол.
			time_table_dict[name] = TimeTable(name, 
												open_time= open_time,
												close_time= close_time,
												interval= interval,
												passing_time= passing_time)
			#Генерим клавиатуру личных дистанций
			if len(row) == Loader.NUM_OF_KEYS_IN_ROW_FOR_DIST:
				dist_personal_keyboard.append(row)
				row = []
			row.append(name)

		# Заканчиваем создание регулярки для распознования одного из названий дистанции
		re_str_pesr_disr += ")$"

		# Заканчиваем генерить клавиатуру личных дистанций
		dist_personal_keyboard.append(row)
		dist_personal_keyboard.append([ COMPLETE_CHOOSING])
		row = []
		print(type(dist_personal_keyboard))


		# Генерим клавиатуру этапов дистанций
		distances_dict = {'mountain_simple': stages_mountain_simple_keyboard, 'mountain_complex': stages_mountain_complex_keyboard,
						  'fox_hunting': stages_fox_hunting_keyboard, 'adventure': stages_adventure_keyboard,
						  'water_katamaran': stages_water_katamaran_keyboard, 'bike':stages_bike_keyboard, 'pedestrian': stages_pedestrian_keyboard}
		for p_dist in self.info_pars.at(Loader.pers_dist_group_name):
			dist_params = self.info_pars.at(p_dist)
			for param in dist_params:
				try:
					if re.findall(r'\bst[\d]+\b', param):
						distances_dict[p_dist].append(self.info_pars.at(p_dist)[param])
						#print(distances_dict[p_dist])
				except Exception as e:
					print('ошибка але')
					print(e.args)
		for g_dist in self.info_pars.at(Loader.group_dist_group_name):
			dist_params = self.info_pars.at(g_dist)
			for param in dist_params:
				try:
					if re.findall(r'\bst[\d]+\b', param):
						distances_dict[g_dist].append(self.info_pars.at(g_dist)[param])
						#print(distances_dict[p_dist])
				except Exception as e:
					print('ошибка але')
					print(e.args)
		# Закончила генерить клавиатуру этапов дистанций
		#print(stages_mountain_complex_keyboard)
		#print(distances_dict)

		#############################################################
		#Загрузка информации о дистанциях
		#Мы верим, что груповые и пешеходыне дистанции не пересекаются
		for dist_name in dist_personal_dict:
			dist_personal_dict[dist_name].load_protocol(dist_name)

			time_table_dict[dist_name].load_TT(dist_name)


		#############################################################
		#загрузка актуальной информации о пользователях
		users = Users()
		users.load_users()
		
		#print(users.user_dict)
		
		##############################################################
		#загрузка актуальной информации о судьях
		
		judges = Judges()
		try:
			judges.load_aut_info()
			judges.load_judge_dict()
			# вообще, тут надо сделать сплит, дабы из текста сотворить список.
		
		except Exception as e:
			print(e.args)
		
		##############################################################
		#загрузка актуальной информации о командах
		teams = Teams()
		try:
			teams.load_teams()
		except Exception as e:
			print(e.args)

