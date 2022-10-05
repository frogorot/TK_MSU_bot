from datetime import time
from datetime import timedelta
import random
import toml
import pandas as pd
import pathlib 

#SECURE_DIRECTORY_NAME = 'secure_info'
#INFO_DIRECTORY_NAME = 'load_info'
#SHEETS_DIRECTORY_NAME = 'sheets'
SHEET_EXTENTION = '.xlsx'
# идеи
# slot - это строка(пустая или непустая) в стартовом протоколе
class Parser:
	def __init__(self):
		self.parsed_toml = None

	def load_toml(self, ini_file: str):
		""" ini_file shoud be a full name"""
		#path = pathlib.Path(ini_file)
		#str_path = str(path)
		print(ini_file)

		self.parsed_toml = toml.load(ini_file)

	def at(self, atribute: str):
		"""Returns value of "atribute" from "ini_file"."""
		if self.parsed_toml != None and atribute in self.parsed_toml.keys():
			return self.parsed_toml[atribute]
		else: 
			return None


class Slot:
	def __init__(self, order_number, start: time, interval: time, is_free):
		self.order_number = order_number
		self.start = start
		self.interval = interval
		self.is_free = is_free


def is_seg_nin_seg_list(moment: (time, time), segment_list: list(time, time))-> bool: 
	# Проверяет, находится пересекается ли отрезок с каким-то отрезком из списка

	for segment in segment_list:
		if moment(1) >= segment[0] and moment(0) <= segment[1]: # Проще всего проверить истинность, если взять отрицание
			return False
	else:
		return True


def is_seg_nin_seg_list(left_point: time, length: timedelta, segment_list: list(time, time))-> bool: 
	# Проверяет, находится пересекается ли отрезок, заданный лывой точкой и длинной, с каким-то отрезком из списка
	right_point = left_point + length
	for segment in segment_list:
		if left_point >= segment[0] and right_point <= segment[1]: # Проще всего проверить истинность, если взять отрицание
			return False
	else:
		return True
	

class TimeTable:
	# open_time - время открытия дистанции, close_time - время закрытия дистанции
	def __init__(self, distance: str, open_time: time, close_time: time, interval: time, passing_time: time):
		self.name = distance
		self.open_time = open_time
		self.close_time = close_time
		self.interval = interval
		self.dist_passing_time = passing_time
		self.table = [ Slot(from_start_time_to_num_default(slot_time), slot_time, interval, True)  for slot_time in gene_table(open_time, close_time, interval) ] # пустой стартовый протокол 
		self.table_of_free = { slot.order_number : slot for slot in self.table } # Не список, так как свободные слоты могут идти хаотично. Индексация всё равно по порядковому номеру слотов

	def gene_table(open_time, close_time, interval):
		i = open_time
		while i <= (close_time - interval):
			yield i
			i += interval

	def from_start_time_to_num_default(current_start_time): #конверитирует время старта слота в его номер
		return (current_start_time - self.open_time) / self.interval;
		#self.bounds_of_free = {self.table[0].start : self.table[0]} #< Список "границ" свободных в непрервном отрезке свободных: ++--+-+++ - здесь должны быть 0, 1, 4, 6, 8. 

	def is_time_free(self, time_for_check) -> (bool, time): # возвращает самое раннее время старта до time
		if time_for_check < self.open_time or time_for_check > self.close_time:
			return (False, 0)
		else:
			for slot in self.table: # Можно оптимизировать, но лень
				if slot.is_free and slot.start <= time_for_check and time_for_check <= slot.start + slot.interval:
					return (True, slot.start)
			else:
				return (False, 0)
	
	def booking_slot(self, rand: bool) -> (int, time, time): # резервация слота. Возвращает пару: (время старта, предполагаемое время финиша)
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

		return (cur_slot.order_num, cur_slot.start, cur_slot.start + self.dist_passing_time)

	def booking_slot(self, rand: bool, list_of_unavailable: list(time,time) = None) -> (int, time, time):
		cur_slot;
		if rand:
			rand_pos = random.randint(0, len(self.table)-1)
			if self.table[rand_pos].is_free:
				cur_slot = self.table[rand_pos]
				#return (rand_pos, self.table[rand_pos].start, self.table[rand_pos].start + self.dist_passing_time)
			
			else:
				awaleble_free_slots = []
				if list_of_unavailable == None:
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
					cur_slot = self.table_of_free[nearest_slot_num]
					#return (nearest_slot_num, self.table_of_free[nearest_slot_num], self.table_of_free[nearest_slot_num] + self.dist_passing_time)

			#for slot_num in self.table_of_free: # ищем первое свободное после случайного
			#	if slot_num >= 
			#	cur_slot = self.table_of_free[slot_num]
			#	if cur_slot.is_free:
			#		cur_slot.is_free = False
			#		break
			#		#return (cur_slot.start, cur_slot.start + self.dist_passing_time)
			#else: 
			#	down_free_slots;
			#	if list_of_unavailable == None:
			#		down_free_slots = [slot_num for slot_num in self.table_of_free 
			#			if slot_num >= rand_pos]
			#	else:
			#		down_free_slots = [slot_num for slot_num in self.table_of_free 
			#			if slot_num >= rand_pos and 
			#				is_seg_nin_seg_list( self.table_of_free[slot_num].start, self.dist_passing_time, list_of_unavailable) ]
			#
			#
			#	for slot_num in down_free_slots: # Если после все заняты, ищем до.
			#		cur_slot = self.table_of_free[slot_num]
			#		if cur_slot.is_free:
			#			cur_slot.is_free = False
			#			pass
			#			#return (cur_slot.start, cur_slot.start + self.dist_passing_time)
			#	else:
			#		raise Exception("TimeTable.book_slot:: Nothing free.") # Если все заняты, у нас проблемы;)
			#		return (0,0,0)
		#else:
			#list_of_interest;
			#if list_of_unavailable == None:
			#	list_of_interest = self.table_of_free.keys()
			#else:
			#	list_of_interest = [slot_num for slot_num in self.table_of_free 
			#			if is_seg_nin_seg_list( self.table_of_free[slot_num].start, self.dist_passing_time, list_of_unavailable)]

		elif list_of_unavailable == None:
			if self.table_of_free != None:
				cur_slot = self.table_of_free[0]
				#return (self.table_of_free[0].order_number, self.table_of_free[0].start, self.table_of_free[0] + self.dist_passing_time)
			else:
				raise Exception("TimeTable.book_slot:: Nothing free.") # Если все заняты, у нас проблемы;)
				return (0,0,0)
		else:
			for slot_num in self.table_of_free: # Можно оптимизировать, но лень - проверяем всю табличку(а можем только свободные)
				if is_seg_nin_seg_list( self.table_of_free[slot_num].start, self.dist_passing_time, list_of_unavailable):
					cur_slot = self.table_of_free[slot_num]
					#return (self.table_of_free[slot_num].order_number, self.table_of_free[slot_num].start, self.table_of_free[slot_num] + self.dist_passing_time)
			else:
				raise Exception("TimeTable.book_slot:: Nothing free.") # Если все заняты, у нас проблемы;)
				return (0,0,0)
		
		cur_slot.is_free = False
		return (cur_slot.order_num, cur_slot.start, cur_slot.start + self.dist_passing_time)


	def free_slots(self):
		return table_of_free

	def getTable(self) -> list[Slot]:
		return self.table

	def to_dafaframe(self): # список в датафрейм
		df_table = pd.DataFrame({
			'Start_times' : [slot.start for slot_time in self.table],
			'Free_slot' : [slot.is_free for slot_time in self.table]
			},
			index = [slot.order_number for slot_time in self.table])
		return df_table
	
	def setTable(self, new_table: list[Slot]):
		self.table = new_table

	def TableFromDF(self, df: pd.DataFrame): # датафрейм в список
		if (not 'Start_times' in  df.columns) or (not 'Free_slot' in  df.columns):
			raise Exception('TableFromDF:: wrond df, there no some columns')
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

	def setSlot(self, slot_num: int, start_time: time, interval: time, is_free: bool): # добавляет слот с заданными параметрами в конец списка
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
	def __init__(self):
		list_of_params = ['Tg_id', 
						  'Autentificated', # 'Autentificated' - факт аутентификации(trur or false(мб так, Лёха не уверен, надо смотреть код))
						  'Name', 
						  'Status', 
						  'Distances', 
						  'Stages'] 
		self.filename_dict = None
		self.filename_aut = None
		self.judge_dict = pd.DataFrame(columns = list_of_params) #Дистанции - список, этапы - словарь = {дистанция:этап}
		self.judge_dict.set_index('Tg_id')
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
		#self.filename_aut = self.filename_aut
		with open(self.filename_aut + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + ".aut", 'W') as file: #time - чтобы были логи
			for line in self.judge_autentification:
				string = line + ' | ' + self.judge_autentification[line] + "\n"
				file.write(string)

	def write_judge_list(self):
		#self.filename_dict = self.filename_dict 
		self.judge_dict.to_excel(self.filename_dict + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + SHEET_EXTENTION)

	# Можно сделать сканер директории и автоматически загружать последний по времени файл.
	def load_aut_info(self, filename: str = None): #filename без .xlsx
		if filename != None:
			self.filename_aut = filename
		else:
			if self.filename_aut == None:
				raise Exseption("Judges::load_aut_info: empty file name and empty self.filename_aut. I can't contine load")
			
		with open(self.filename_aut + SHEET_EXTENTION, 'r') as file:
			for line in file:
				namesize = line.find(' | ')
				judgename = line[0 : namesize]
				judgepassword = line[namesize + 3 : ]
				self.judge_autentification[judgename] = (judgepassword, False, 0, 0) # tg_id : (пароль, вошёл ли в учётку,число неуспешных попыток, время последней попытки)
	# Можно сделать сканер директории и автоматически загружать последний по времени файл.
	def load_judge_dict(self, filename: str): #загружам данные judge_dict
		if filename != None:
			self.filename_dict = filename
		else:
			if self.filename_dict == None:
				raise Exseption("Judges::load_judge_list: empty file name and empty self.filename_dict. I can't contine load")
		
		self.judge_dict = pd.read_excel(INFO_DIRECTORY_NAME + self.filename_dict + SHEET_EXTENTION)
		self.judge_dict.set_index('Tg_id')

		if not set(list_of_params).issubset(self.judge_dict.columns):
			self.judge_dict = pd.DataFrame(columns = list_of_params) #Дистанции - список, этамы - словарь = {дистанция:этап}
			self.judge_dict.set_index('Tg_id')
			raise Exsepton("Judges::load_judge_list: Wrong data in filename=" + filename + ". There is no Judges::list_of_params.")

	def try_to_autentificate_judge(self, judge_tg_id, judge_password: str) -> bool: #челик вводит пароль, ключ tg_id
		if judge_tg_id in self.judge_autentification.keys():
			if self.judge_autentification[judge_tg_id] == judge_password:
				user_info = self.judge_autentification[judge_tg_id]
				self.judge_autentification[judge_tg_id] = (user_info[0], True, user_info[2], time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) )
				return True
			else:
				user_info = self.judge_autentification[judge_tg_id]
				self.judge_autentification[judge_tg_id] = (user_info[0], user_info[1], user_info[2] + 1, time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) )
				return False
		else:
			return False

	def is_judge_autentificate(self, judge_tg_id) -> bool:
		if judge_tg_id in self.judge_autentification.keys():
			return self.judge_autentification[judge_tg_id][IS_AUT] # Поскольку у нас словарь четвёрок, надо найти запись в словаре и взять состояние аутентификации из четвёрки.
			# Да, мерзко.
	

class Users:
	MALE, FEMALE = range(2)
	def __init__(self):
		list_of_params = ['Tg_id', 
						  'Name', 
						  'Age', 
						  'Sex', 
						  'University', 
						  'Facility', 
						  'Distances']
		self.filename = None
		self.user_dict = pd.DataFrame(columns = list_of_params) #Дистанции - список, этапы - словарь = {дистанция:этап}
		self.user_dict.set_index('Tg_id')

	def write_users(self):
		self.user_dict.to_excel(self.filename + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + SHEET_EXTENTION)

	def load_users(self, filename: str = None):
		if filename != None:
			self.filename = filename
		else:
			if self.filename == None:
				raise Exseption("Users::load_users: empty file name and empty self.filename. I can't contine load")
			
		self.user_dict = pd.read_excel(self.filename + SHEET_EXTENTION)
		self.user_dict.set_index('Tg_id')
		if not set(list_of_params).issubset(self.user_dict.columns): #проверка что нам дали адекватный файл(например не файл с судьями)
			self.user_dict = pd.DataFrame(columns = list_of_params) #Дистанции - список, этамы - словарь = {дистанция:этап}
			self.user_dict.set_index('Tg_id')
			raise Exsepton("Users::load_users: Wrong data in filename=" + filename + ". There is no Users::list_of_params.")

class Teams:
	def __init__(self, major_id):
		list_of_params = ['Tg_id_major', 
						  'Name', 
						  'Distance', 
						  'Slot_num', 
						  'Member_id', 
						  'Facility', 
						  'Distances']
		self.filename = None
		self.team_dict = pd.DataFrame(columns = list_of_params) #Дистанции - список, этапы - словарь = {дистанция:этап}
		self.team_dict.set_index(['Tg_id_major', 'Distance'])

	def write_teams(self):
		self.team_dict.to_excel(self.filename + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + SHEET_EXTENTION)

	def load_users(self, filename: str = None):
		if filename != None:
			self.filename = filename
		else:
			if self.filename == None:
				raise Exseption("Users::load_users: empty file name and empty self.filename. I can't contine load")
		
		self.team_dict = pd.read_excel(self.filename + SHEET_EXTENTION)
		self.team_dict.set_index(['Tg_id_major', 'Distance'])

		if not set(list_of_params).issubset(self.team_dict.columns):
			self.team_dict = pd.DataFrame(columns = list_of_params) #Дистанции - список, этамы - словарь = {дистанция:этап}
			self.team_dict.set_index(['Tg_id_major', 'Distance'])
			raise Exsepton("Users::load_users: Wrong data in filename=" + filename + ". There is no Users::list_of_params.")

#class Judge:
#    MAJOR, LINEAR = range(2)
#        
#    def __init__(self, tg_id):
#        self.tg_id = tg_id # realy is a chat_id
#        self.name = None # Фио
#        self.status = LINEAR
#        self.diastances = [] 
#        self.stage = [] # Этапы дистанций
#
#
#class User:
#    def __init__(self, tg_id):
#        self.tg_id = tg_id # realy is a chat_id
#        self.name = None # Фио
#        self.age = None 
#        self.sex = None
#        self.university = None
#        self.facility = None
#        self.diastances = []
#user_dict = {}
#
#class Team:
#    def __init__(self, major_id):
#        self.tg_id_major = major_id #tg_id регистрирующего команду
#        self.name = None
#        self.distance = None
#        self.slot_num = None
#        self.member_id = []
#        self.member_id.append(major_id)
#    def __init__(self, user: User, distance): # команда на личную дистанцию
#        self.tg_id_major = user.tg_id 
#        self.name = user.name
#        self.distance = distance
#        self.slot_num = None
#        self.member_id = []
#        self.member_id.append(user.tg_id)
#team_dict = {}


class DistanceResults:
	def __init__(self, name):
		self.name = name
		self.table = pd.DataFrame()

	def loadProtocol(self, df: pd.DataFrame):
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
dist_dict = {}
dist_print_pattern = []

def print_my_class(tt):
	if hasattr(tt, 'to_dafaframe'):
		cur_time = time.localtime(time.time())
		name = str()
		if hasattr(tt, 'name'):
			name= 'sheets\\' + type(tt).__name__ + tt.name + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + ".xlsx"
		else:
			name= 'sheets\\' + type(tt).__name__ + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + ".xlsx"
		df = tt.to_dafaframe()
		df.to_excel(excel_writer = "sheets\ " + type(tt) + time.ctime(time.time()) + ".xlsx")
