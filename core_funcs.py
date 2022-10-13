import random
import toml
import pandas as pd
#import pathlib 
import time

#SECURE_DIRECTORY_NAME = 'secure_info'
#INFO_DIRECTORY_NAME = 'load_info'
#SHEETS_DIRECTORY_NAME = 'sheets'
SHEET_EXTENTION = '.xlsx'
AUTENTIFICATION_EXTENTION = '.aut'
ARCHIVE_PATH = 'Archive/'

COMPLETE_CHOOSING = 'Всё'

TEAM_REG_PREFIX = "TEAM_REG_"

TEAM_NAME_LENTH = 50

#class Containers:
secure_directory = None
info_directory = None

time_table_dict = {}

dist_personal_dict = {}
dist_personal_keyboard = []
re_str_pesr_disr = None

dist_group_dict = {}
dist_group_keyboard = []
dist_group_team_members_count = {}
re_str_group_disr = None


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


class Slot:
	def __init__(self, order_number: int, start: int, interval: int, is_free):
		self.order_number = order_number
		self.start = start
		self.interval = interval
		self.is_free = is_free


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

class TimeTable:
	# open_time - время открытия дистанции, close_time - время закрытия дистанции
	def from_start_time_to_num_default(self, current_start_time) -> int: #конверитирует время старта слота в его номер
		return int((current_start_time - self.open_time) / self.interval);

	def __init__(self, distance: str, open_time: int, close_time: int, interval: int, passing_time: int):
		self.name = distance
		self.open_time = open_time
		self.close_time = close_time
		self.interval = interval
		self.dist_passing_time = passing_time
		self.table = [ Slot(int(from_start_time_to_num_default(slot_time, self.open_time, self.interval)), slot_time, interval, True)
				for slot_time in gene_table(open_time, close_time, interval) ] # пустой стартовый протокол 
		self.table_of_free = { slot.order_number : slot for slot in self.table } # Не список, так как свободные слоты могут идти хаотично. Индексация всё равно по порядковому номеру слотов


	def update_free(self, current_time: int):
		for slot_num in self.table_of_free:
			slot = self.table_of_free[slot_num]
			if slot.start < current_time:
				slot.is_free = False
				self.table_of_free.pop(slot_num)

	def is_time_free(self, time_for_check) -> (bool, int): # возвращает самое раннее время старта до int
		if time_for_check < self.open_time or time_for_check > self.close_time:
			return (False, 0)
		else:
			for slot in self.table: # Можно оптимизировать, но лень
				if slot.is_free and slot.start <= time_for_check and time_for_check <= slot.start + slot.interval:
					return (True, slot.start)
			else:
				return (False, 0)
	
	def booking_slot(self, rand: bool) -> (int, int, int): # резервация слота. Возвращает пару: (время старта, предполагаемое время финиша)
		cur_slot;
		if rand:
			rand_pos = random.randint(0, len(self.table)-1)
			top_free_slots = [slot_num for slot_num in self.table_of_free if slot_num >= rand_pos]
			for slot_num in top_free_slots: # ищем первое свободное после случайного
				cur_slot = self.table_of_free[slot_num]
				if cur_slot.is_free:
					cur_slot.is_free = False
					pass
					#return (cur_slot.start, cur_slot.start + self.dist_passing_time)
			else: 
				down_free_slots = [slot_num for slot_num in self.table_of_free if slot_num <= rand_pos]
				for slot_num in down_free_slots: # Если после все заняты, ищем до.
					cur_slot = self.table_of_free[slot_num]
					if cur_slot.is_free:
						cur_slot.is_free = False
						pass
						#return (cur_slot.start, cur_slot.start + self.dist_passing_time)
				else:
					raise Exception("TimeTable.book_slot:: Nothing free.") # Если все заняты, у нас проблемы;)
					return (0,0,0)
		else:
			for slot_num in self.table_of_free: # Можно оптимизировать, но лень - проверяем всю табличку(а можем только свободные)
				cur_slot = self.table_of_free[slot_num]
				if cur_slot.is_free:
					cur_slot.is_free = False
					pass
					#return cur_slot.start, cur_slot.start + self.dist_passing_time)
			else:
				raise Exception("TimeTable.book_slot:: Nothing free.") # Если все заняты, у нас проблемы;)
				return (0,0,0)

		return (cur_slot.order_number, cur_slot.start, cur_slot.start + self.dist_passing_time)

	def booking_slot(self, rand: bool, list_of_unavailable: list = []) -> (int, int, int):
		cur_slot = None
		if rand:
			rand_pos = random.randint(0, len(self.table)-1)

			if self.table[rand_pos].is_free and is_seg_nin_seg_list( self.table[rand_pos].start, self.dist_passing_time, list_of_unavailable):
				cur_slot = self.table.pop(rand_pos)
				#return (rand_pos, self.table[rand_pos].start, self.table[rand_pos].start + self.dist_passing_time)
			
			else:
				awaleble_free_slots = []
				if list_of_unavailable == []:
					awaleble_free_slots = self.table_of_free.keys() 
				else:
					awaleble_free_slots = [slot_num for slot_num in self.table_of_free 
						if is_seg_nin_seg_list( self.table_of_free[slot_num].start, self.dist_passing_time, list_of_unavailable) ]
				
				nearest_slot_num = awaleble_free_slots[0]
				min_distance = abs(nearest_slot_num - rand_pos)

				for slot_num in awaleble_free_slots:
					if abs(slot_num - rand_pos) < min_distance:
						nearest_slot_num = slot_num
						min_distance = abs(slot_num - rand_pos)
				else:
					cur_slot = self.table_of_free.pop(nearest_slot_num)
		elif list_of_unavailable == []:
			if self.table_of_free != None:
				cur_slot = self.table_of_free.pop(0)
				#return (self.table_of_free[0].order_number, self.table_of_free[0].start, self.table_of_free[0] + self.dist_passing_time)
			else:
				raise Exception("TimeTable.book_slot:: Nothing free.") # Если все заняты, у нас проблемы;)
				return (-1,0,0)
		else:
			for slot_num in self.table_of_free: 
				if is_seg_nin_seg_list( self.table_of_free[slot_num].start, self.dist_passing_time, list_of_unavailable):
					cur_slot = self.table_of_free.pop(slot_num)
					break
					#return (self.table_of_free[slot_num].order_number, self.table_of_free[slot_num].start, self.table_of_free[slot_num] + self.dist_passing_time)
			else:
				raise Exception("TimeTable.book_slot:: Nothing free.") # Если все заняты, у нас проблемы;)
				return (-1,0,0)
		
		cur_slot.is_free = False
		return (cur_slot.order_number, cur_slot.start, cur_slot.start + self.dist_passing_time)
		

	def free_slots(self):
		return table_of_free

	def getTable(self) -> list[Slot]:
		return self.table

	def to_dafaframe(self) -> pd.DataFrame: # список в датафрейм
		df_table = pd.DataFrame({
			'Start_times' : [slot.start for slot in self.table],
			'Free_slot' : [slot.is_free for slot in self.table]
			},
			index = [slot.order_number for slot in self.table])
		return df_table
	
	def retun_filename(self) -> str:
		return info_directory + self.name + SHEET_EXTENTION

	def write_TT(self, filename: str = ""):
		df = self.to_dafaframe()

		time_str = time.strftime("-%m.%d.%Y_%H-%M-%S", time.localtime(time.time()))

		write_file_name = ""
		if filename == "":
			write_file_name += self.name
		else:
			write_file_name += filename

		df.to_excel(info_directory + ARCHIVE_PATH + write_file_name +  time_str + SHEET_EXTENTION)
		df.to_excel(info_directory + write_file_name + SHEET_EXTENTION)

	def setTable(self, new_table: list[Slot]):
		self.table = new_table

	def TableFromDF(self, df: pd.DataFrame): # датафрейм в список
		if (not 'Start_times' in  df.columns) or (not 'Free_slot' in  df.columns):
			raise Exception('TableFromDF:: wrong df, there no some columns')
		else:
			self.table.clear()
			for df_ind in df.index():
				if not df_ind + 1 in df.index():
					interval = 15*60 #Eeee, magick number!
				else:
					interval = df[df_ind + 1]['Start_times'] - df[df_ind]['Start_times']
				self.table.append( Slot(df_ind, df[df_ind]['Start_times'], interval,  df[df_ind]['Free_slot']) )
				if df[df_ind]['Free_slot']:
					self.table_of_free[df_ind] = self.table[-1] # Нужно проверить

	def load_TT(self, filename: str = ""):
		load_file_path = info_directory
		if filename == "":
			load_file_path += self.name + SHEET_EXTENTION
		else:
			load_file_path += filename + SHEET_EXTENTION

		self.table = pd.read_excel(load_file_path)
		self.table_of_free = { slot.order_number : slot for slot in self.table if slot.is_free }

	def setSlot(self, slot_num: int, start_time: int, interval: int, is_free: bool): # добавляет слот с заданными параметрами в конец списка
		if slot_num > (len(self.table) - 1): # Если номер больше имевшихся, то заполняем "пропуск" дефолтными слотами
			for slot in range(len(self.table) - 1, slot_num):
				 self.table.append( Slot(slot, self.open_time + slot*self.interval, interval, True) )
				 self.table_of_free[slot] = self.table[-1] # Т.к. они точно свободные.
		else:
			if slot_num in self.table_of_free.keys() and not is_free: #Если номер имеется, то, возможно, надо удалить его из свободных
				self.table_of_free.pop(slot_nun)
		
		self.table[slot_num] = Slot(slot, start_time, interval, is_free)
		if is_free:
			self.table_of_free[slot_num] = self.table[slot_num]

	def updateTable(self):
		""" Применяется после setSlot, чтобы выравнять времена старта и интервалы: если изменённый - длиннее interval, то следующий старт реально произойдёт позже.
		Возвращяет список подвинувшихся слотов."""
		expected_start = self.open_time
		moving_slots = []
		outer_slot_num = 0
		for slot in self.table:
			if slot.ordere_num != outer_slot_num:
				moving_slots.append(slot)
				slot.ordere_num = outer_slot_num
			if slot.start != expected_start:
				moving_slots.append(slot)
			slot.start = expected_start
			expected_start =  slot.start + slot.interval
			outer_slot_num += 1

		return moving_slots

class Judges:
	MAJOR, LINEAR = range(2) # - 'Status', 'stage' - этапы
	PASSWORD, IS_AUT, NUM_OF_FAILS, TIME_OF_LAST_TRY = range(4)

	list_of_params = ['Tg_id', 
						  'Name', 
						  'Status', 
						  'Distances', 
						  'Stages'] 

	def __init__(self):
		self.filename_dict = "Judges list"
		self.filename_aut = "Judges autentification info"
		self.judge_dict = pd.DataFrame(columns = Judges.list_of_params) #Дистанции - список, этапы - словарь = {дистанция:этап}
		self.judge_dict = self.judge_dict.set_index('Tg_id')
		self.judge_autentification = {} # зашел ли судья с этим паролем или нет # tg_id : (пароль, вошёл ли в учётку,число неуспешных попыток, время последней попытки)
		#aut_time_delay = [0, 10, 20] # в каждом окне по 3 попытки
	
	#ниже создаем и работаем для безопасности с 2 листами: judge_dict(5) and judge_autentification(judge, password)
	def new_judge(self, tg_id, name: str, dist, stage) -> (bool, str):
		#if not tg_id in self.judge_dict.index:
			#new_line = pd.DataFrame({'Tg_id': [tg_id],'Autentificated':[False], 'Name' : [name],'Status' : [LINEAR], 'Distances' : [dist], 'Stages' : [stage] })
			#self.judge_dict = pd.concat([self.judge_dict, new_line], ignore_index = True)
		self.judge_dict[tg_id] = [ False, name, LINEAR, dist, stage]

		self.judge_autentification[tg_id] = random.randint(10000, 99999) #??? поправить рандомайзер который не генерит одинаковые
		write_aut_info(self)
		write_judge_list(self)
		return (True, self.judge_autentification[tg_id])

	def write_aut_info(self): # записываем id из tg и пароли

		time_str = time.strftime("-%m.%d.%Y_%H-%M-%S", time.localtime(time.time()))
		
		full_filename = secure_directory + ARCHIVE_PATH + self.filename_aut + time_str + AUTENTIFICATION_EXTENTION
		with open(full_filename, mode= 'w') as file: #int - чтобы были логи

			for line in self.judge_autentification:
				string = line + ' | ' + self.judge_autentification[line] + "\n"
				file.write(string)
		
		full_filename = secure_directory + self.filename_aut + AUTENTIFICATION_EXTENTION
		with open(full_filename, mode= 'w') as file: #int - чтобы были логи
			for line in self.judge_autentification:
				string = line + ' | ' + self.judge_autentification[line] + "\n"
				file.write(string)

	def write_judge_list(self):
		#self.filename_dict = self.filename_dict
		if self.filename_dict == None:
			self.filename_dict = "Judges_list"

		time_str = time.strftime("-%m.%d.%Y_%H-%M-%S", time.localtime(time.time()))

		self.judge_dict.to_excel(info_directory + ARCHIVE_PATH + self.filename_dict + time_str + SHEET_EXTENTION)
		self.judge_dict.to_excel(info_directory + self.filename_dict + SHEET_EXTENTION)

	def retun_filename(self) -> str:
		write_file_name = ""
		if self.filename_dict == "":
			write_file_name += "Judges_list"
		else:
			write_file_name += self.filename_dict
		return info_directory + write_file_name + SHEET_EXTENTION

	# Можно сделать сканер директории и автоматически загружать последний по времени файл.
	def load_aut_info(self, filename: str = "Judjes autentification info"): #filename без .xlsx
		if filename != None:
			self.filename_aut = filename
		else:
			if self.filename_aut == None:
				raise Exseption("Judges::load_aut_info: empty file name and empty self.filename_aut. I can't contine load")
		
		full_filename = secure_directory + self.filename_aut + AUTENTIFICATION_EXTENTION
		with open(full_filename, mode= 'r') as file:
			for line in file:
				namesize = line.find(' | ')
				judgename = line[0 : namesize]
				judgepassword = line[namesize + 3 : ]
				self.judge_autentification[judgename] = (judgepassword, False, 0, 0) # tg_id : (пароль, вошёл ли в учётку,число неуспешных попыток, время последней попытки)

	# Можно сделать сканер директории и автоматически загружать последний по времени файл.
	def load_judge_dict(self, filename: str = "Judges_list"): #загружам данные judge_dict
		if filename != None:
			self.filename_dict = filename
		else:
			if self.filename_dict == None:
				raise Exseption("Judges::load_judge_list: empty file name and empty self.filename_dict. I can't contine load")
		
		self.judge_dict = pd.read_excel(info_directory + self.filename_dict + SHEET_EXTENTION)

		if not set(Judges.list_of_params).issubset(self.judge_dict.columns):
			self.judge_dict = pd.DataFrame(columns = Judges.list_of_params) #Дистанции - список, этамы - словарь = {дистанция:этап}
			raise Exsepton("Judges::load_judge_list: Wrong data in filename=" + filename + ". There is no Judges::list_of_params.")

		self.judge_dict.set_index('Tg_id')

	# Попытка аутентификации судьи
	def try_to_autentificate_judge(self, judge_tg_id, judge_password: str) -> bool: #челик вводит пароль, ключ tg_id
		if judge_tg_id in self.judge_autentification.keys():
			if self.judge_autentification[judge_tg_id] == judge_password:
				user_info = self.judge_autentification[judge_tg_id]
				self.judge_autentification[judge_tg_id] = (user_info[0], True, user_info[2], int.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) )
				return True
			else:
				user_info = self.judge_autentification[judge_tg_id]
				self.judge_autentification[judge_tg_id] = (user_info[0], user_info[1], user_info[2] + 1, int.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) )
				return False
		else:
			return False

	def is_judge_autentificate(self, judge_tg_id) -> bool:
		if judge_tg_id in self.judge_autentification.keys():
			return self.judge_autentification[judge_tg_id][IS_AUT] # Поскольку у нас словарь четвёрок, надо найти запись в словаре и взять состояние аутентификации из четвёрки.
			# Да, мерзко.
	

class Users:
	MALE, FEMALE = range(2)
	RES_TIME = "Reserved times"

	list_of_params = ['Tg_id', 
						  'Name', 
						  'Age', 
						  'Sex', 
						  'University', 
						  'Facility', 
						  RES_TIME]

	def __init__(self):
		self.filename = "Users"
		self.user_dict = pd.DataFrame(columns = Users.list_of_params) #Дистанции - список, этапы - словарь = {дистанция:этап}
		self.user_dict = self.user_dict.set_index('Tg_id')

	def retun_filename(self) -> str:
		write_file_name = ""
		if self.filename == "":
			write_file_name += "Users"
		else:
			write_file_name += self.filename
		return info_directory + write_file_name + SHEET_EXTENTION

	def write_users(self):
		if self.filename == None:
			self.filename = "Users"

		time_str = time.strftime("-%m.%d.%Y_%H-%M-%S", time.localtime(time.time()))

		self.user_dict.to_excel(info_directory + ARCHIVE_PATH + self.filename + time_str + SHEET_EXTENTION)
		self.user_dict.to_excel(info_directory + self.filename + SHEET_EXTENTION)

	def load_users(self, filename: str = "Users"):
		if filename != None:
			self.filename = filename
		else:
			if self.filename == None:
				raise Exseption("Users::load_users: empty file name and empty self.filename. I can't contine load")
		
		try:
			self.user_dict = pd.read_excel(info_directory + self.filename + SHEET_EXTENTION)

			if not set(Users.list_of_params).issubset(self.user_dict.columns): #проверка что нам дали адекватный файл(например не файл с судьями)
				self.user_dict = pd.DataFrame(columns = Users.list_of_params) #Дистанции - список, этамы - словарь = {дистанция:этап}
				raise Exsepton("Users::load_users: Wrong data in filename=" + filename + ". There is no Users::list_of_params.")

		except Exception as e:
			print(e.args)
		
		# Устанавливаем индекс Tg_id. Если это сделать раньше, то проапдёт соответствующая колонка и не красиво проверять
		self.user_dict = self.user_dict.set_index('Tg_id')

		# Перегоняем строку в список пар.
		for user in self.user_dict.index:
			user_res_time = self.user_dict.at[user, Users.RES_TIME]
			if user_res_time == '[]':
				self.user_dict.at[user, Users.RES_TIME] = []
			else:
				# Проигнорировали скобочки в начале и конце, разбили в список, причём в конец добавили ", ", чтобы привести последнюю скобку к тому же виду, что и остальные: "(235, 578"
				# 
				# Но список состоял из пар вида "(235, 578". Снова игнорируем левую скобочку в каждой паре и сплитим по запятой.
				#
				# Ещё список может быть пустой. Ещё из-за отбирания скобки у последней пары в конце есть ''. 
				self.user_dict.at[user, Users.RES_TIME] = [ 
					tuple(
						int(x) for x in pair[1:].split(', ')
						) 
					for pair in (user_res_time[1:-1] + ", ").split('), ') 
						if pair != '']

class Teams:

	MEMBERS_ID = 'Members_id'

	list_of_params = ['Tg_id_major', 
						  'Name', 
						  'Distance', 
						  'Slot_num', 
						  MEMBERS_ID, 
						  'Member_confurm_num']

	def __init__(self):
		self.filename = 'Teams'
		self.team_dict = pd.DataFrame(columns = Teams.list_of_params) #Дистанции - список, этапы - словарь = {дистанция:этап}
		self.team_dict = self.team_dict.set_index(['Tg_id_major', 'Distance'])

	def retun_filename(self) -> str:
		write_file_name = ""
		if self.filename == "":
			write_file_name += 'Teams'
		else:
			write_file_name += self.filename
		return info_directory + write_file_name + SHEET_EXTENTION

	def write_teams(self):
		if self.filename == None:
			raise Exseption("Teams::write_teams: empty file name and empty self.filename. I can't contine load")

		time_str = time.strftime("-%m.%d.%Y_%H-%M-%S", time.localtime(time.time()))
		# Пишем два файла - один - для истории, второй - подменяет актуальный
		self.team_dict.to_excel(info_directory + ARCHIVE_PATH + self.filename + time_str + SHEET_EXTENTION)
		self.team_dict.to_excel(info_directory + self.filename + SHEET_EXTENTION)

	def load_teams(self, filename: str = 'Teams'):
		if filename != None:
			self.filename = filename
		else:
			if self.filename == None:
				raise Exseption("Teams::load_teams: empty file name and empty self.filename. I can't contine load")
		
		self.team_dict = pd.read_excel(info_directory + self.filename + SHEET_EXTENTION)

		if not set(Teams.list_of_params).issubset(self.team_dict.columns):
			self.team_dict = pd.DataFrame(columns = Teams.list_of_params) #Дистанции - список, этамы - словарь = {дистанция:этап}
			raise Exsepton("Teams::load_teams: Wrong data in filename=" + filename + ". There is no Teams::list_of_params.")

		self.team_dict = self.team_dict.set_index(['Tg_id_major', 'Distance'])

		# Перегоняем строку в список пар.
		for team in self.team_dict.index:
			team_members_id = self.team_dict.at[team, Teams.MEMBERS_ID]
			if team_members_id == '[]':
				self.team_dict.at[team, Teams.MEMBERS_ID] = []
			else:
				# Проигнорировали скобочки в начале и конце, разбили в список, причём в конец добавили ", ", чтобы привести последнюю скобку к тому же виду, что и остальные: "(235, 578"
				# 
				# Но список состоял из пар вида "(235, 578". Снова игнорируем левую скобочку в каждой паре и сплитим по запятой.
				#
				# Ещё список может быть пустой. Ещё из-за отбирания скобки у последней пары в конце есть ''. 
				self.team_dict.at[team, Teams.MEMBERS_ID] = [id
												for id in (team_members_id[1:-1]).split(', ') 
												if id != '']

class DistanceResults:
	def __init__(self, name):
		self.name = name
		self.table = pd.DataFrame()

	def retun_filename(self) -> str:
		return info_directory + self.name + SHEET_EXTENTION

	def write_protocol(self):
		time_str = time.strftime("-%m.%d.%Y_%H-%M-%S", time.localtime(time.time()))

		self.table.to_excel(info_directory + ARCHIVE_PATH + self.name + time_str + SHEET_EXTENTION)
		self.table.to_excel(info_directory + self.name + SHEET_EXTENTION)

	def load_protocol(self, filename: str = ""):

		load_file_path = info_directory
		if filename == "":
			load_file_path += self.name + SHEET_EXTENTION
		else:
			load_file_path += filename + SHEET_EXTENTION

		self.table = pd.read_excel(load_file_path)

	def set_protocol(self, df: pd.DataFrame):
		self.table = df

	def addStage(self, name, types = ['start', 'finish', 'penalty']):
		for stage_type in types:
			self.table[name + stage_type] = None
	
	def to_dafaframe():
		return self.table
	
	def writesell(self, slot_num: int, stage_name: str, type_of_sell: str, value):
		col_name = stage_name + type_of_sell
		if col_name in self.table.columns:
			self.table.loc[slot_num, col_name] = value
		else:
			raise Exception("DistanceResults.writesell:: There in no column=" + col_name + "in self.table.")

#запись всех данных
async def write_all_data():
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

		global stages_moun_sim_keyboard
		global stages_moun_com_keyboard
		global stages_fox_hunt_keyboard
		global stages_advent_keyboard
		global stages_wat_cat_keyboard
		global stages_bike_keyboard

		global users
		global judges
		global teams
		
		global api_token
		global admin_chat_id


		# Загрузка парсеров
		self.sucere_pars = Parser()
		self.sucere_pars.load_toml(self.run_pars.at('secure_file'))
		self.info_pars = Parser()
		self.info_pars.load_toml(self.run_pars.at('info_file'))
		secure_directory = self.run_pars.at('secure_dir')
		info_directory = self.run_pars.at('info_dir')

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
			#Генерим клавиатуру
			if len(row) == Loader.NUM_OF_KEYS_IN_ROW_FOR_DIST:
				dist_personal_keyboard.append(row)
				row = []
			row.append(name)
		
		# Заканчиваем создание регулярки для распознования одного из названий дистанции
		re_str_pesr_disr += ")$"

		# Заканчиваем генерить клавиатуру
		dist_personal_keyboard.append(row)
		dist_personal_keyboard.append([ COMPLETE_CHOOSING])
		row = []

		#Начинаем генерить клавиатуру для этапов
		#решила, что лучше сделать быстрее, чем красивее с регулярками


		# Обработка информации по групповым дистанциям
		for g_dist in self.info_pars.at(Loader.group_dist_group_name):
			name = self.info_pars.at(Loader.group_dist_group_name)[g_dist]

			dist_group_dict[name] = DistanceResults(name)
			Users.list_of_params.append(name)

			# Создаём регулярку для распознования одного из названий дистанции
			if len(re_str_group_disr) > 2:
				re_str_group_disr += "|"
			re_str_group_disr += name

			dist_params = self.info_pars.at(g_dist) 

			dist_group_team_members_count[name] = dist_params[Loader.team_members_count]

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
			#Генерим клавиатуру
			if len(row) == Loader.NUM_OF_KEYS_IN_ROW_FOR_DIST:
				dist_group_keyboard.append(row)
				row = []
			row.append(name)

		# Заканчиваем создание регулярки для распознования одного из названий дистанции
		re_str_group_disr += ")$"

		# Заканчиваем генерить клавиатуру
		dist_group_keyboard.append(row)

		# К клавиатуре груповых дистанций не надо добавлять "Всё"
		#dist_group_keyboard.append([COMPLETE_CHOOSING])

		##############################################################
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

