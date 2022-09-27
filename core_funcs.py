import time
import random
import toml
import pandas as pd

SECURE_DIRECTORY_NAME = "seqre_info\\"
INFO_DIRECTORY_NAME = "load_info\\" 
SHEETS_DIRECTORY_NAME = "sheets\\" 
SHEET_EXTENTION = ".xlsx"

#def parser:
#    parsed_toml = None
#    def load_toml(atribute: str, ini_file: str):
#        """Returns value of "atribute"from "ini_file".
#        "ini_file" should be a string."""
#        parsed_toml = toml.loads(ini_file)
#        toml.dumps(parsed_toml)
#
#     def pars_toml(atribute: str):
#        """Returns value of "atribute"from "ini_file".
#        "ini_file" should be a string."""
#        if parsed_toml != None and atribute in parsed_toml.keys():
#            return parsed_toml[atribute]
#        else: 
#            return None


class Slot:
     def __init__(self, order_number, start: time, interval: time, is_free):
        self.order_number = order_number
        self.start = start
        self.interval = interval
        self.is_free = is_free
        
class TimeTable:
    def gene_table(open_time, close_time, interval):
        i = open_time
        while i <= (close_time - interval):
            yield i
            i += interval

    def from_start_time_to_num_default(current_start_time):
        return (current_start_time - self.open_time) / self.interval;
    def __init__(self, distance: str, open_time: time, close_time: time, interval: time):
        self.name = distance
        self.open_time = open_time
        self.close_time = close_time
        self.interval = interval
        self.table = [ Slot(from_start_time_to_num_default(slot_time), slot_time, interval, True)  for slot_time in gene_table(open_time, close_time, interval) ]
        #self.bounds_of_free = {self.table[0].start : self.table[0]} #< Список "границ" свободных в непрервном отрезке свободных: ++--+-+++ - здесь должны быть 0, 1, 4, 6, 8. 

    def is_time_free(self, time_for_check) -> (bool, time): # возвращает самое раннее время старта до time
        if time < self.open_time or time > self.close_time:
            return (False, 0)
        else:
            for slot in self.table: # Можно оптимизировать, но лень
                if slot.is_free and slot.start <= time_for_check and time_for_check <= slot.start + slot.interval:
                    return (True, slot.start)
            else:
                return (False, 0)

    def book_slot(self, rand: bool) -> time:
        if rand:
            rand_pos = random.randint(0, len(self.table)-1)
            for slot_num in range(rand_pos, len(self.table)-1): # ищем первое свободное после случайного
                cur_slot = self.table[slot_num]
                if cur_slot.is_free:
                    cur_slot.is_free = False
                    return cur_slot.start
            else: 
                for slot_num in range(0, rand_pos-1): # Если после все заняты, ищем до.
                    cur_slot = self.table[slot_num]
                    if cur_slot.is_free:
                        cur_slot.is_free = False
                        return cur_slot.start
                else:
                    raise Exception("TimeTable.book_slot:: Nothing free.") # Если все заняты, у нас проблемы;)
        else:
            for slot in self.table: # Можно оптимизировать, но лень
                cur_slot = self.table[slot_num]
                if cur_slot.is_free:
                    cur_slot.is_free = False
                    return cur_slot.start
            else:
                raise Exception("TimeTable.book_slot:: Nothing free.") # Если все заняты, у нас проблемы;)

    def free_slots(self):
        return [ self.table[slot] for slot in self.table if self.table[slot].is_free ]

    def getTable(self) -> list[Slot]:
        return self.table

    def to_dafaframe(self):
        df_table = pd.DataFrame({
            'Start_times' : [slot.start for slot_time in self.table],
            'Free_slot' : [slot.is_free for slot_time in self.table]
            },
            index = [slot.order_number for slot_time in self.table])
        return df_table
    
    def setTable(self, new_table: list[Slot]):
        self.table = new_table

    def TableFromDF(self, df: pd.DataFrame):
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

    def setSlot(self, slot_num, start_time, interval, is_free):
        if slot_num > (len(self.table) - 1):
            for slot in range(len(self.table) - 1, slot_num):
                 self.table.append( Slot(slot, self.open_time + slot*self.interval, interval, True) )

        self.table[slot_num] = Slot(slot, start_time, interval, is_free)

    def updateTable(self): 
        """ Применяется после setSlot, чтобы выравнять времена старта и интервалы: если изменённый - длиннее interval, то следующий старт реально произойдёт позже.
        Возвращяет список подвинувшихся слотов."""
        expected_start = self.open_time
        moving_slots = []
        for slot in self.table:
            if slot.start != expected_start:
                moving_slots.append(slot)
            slot.start = expected_start
            expected_start =  slot.start + slot.interval

        return moving_slots

class Judges:
    MAJOR, LINEAR = range(2)
    def __init__(self):
        list_of_params = ['Tg_id', 
                          'Autentificated', 
                          'Name', 
                          'Status', 
                          'Distances', 
                          'Stages']
        self.filename_list = None
        self.filename_aut = None
        self.judge_dict = pd.DataFrame(columns = list_of_params) #Дистанции - список, этамы - словарь = {дистанция:этап}
        self.judge_dict.set_index('Tg_id')
        self.judge_autentification = {} # tg_id : (пароль, вошёл ли в учётку,число неуспешных попыток, время последней попытки)
        #aut_time_delay = [0, 10, 20] # в каждом окне по 3 попытки
    
    def new_judge(self, tg_id, name: str, dist, stage) -> (bool, str):
        #if not tg_id in self.judge_dict.index:
            #new_line = pd.DataFrame({'Tg_id': [tg_id],'Autentificated':[False], 'Name' : [name],'Status' : [LINEAR], 'Distances' : [dist], 'Stages' : [stage] })
            #self.judge_dict = pd.concat([self.judge_dict, new_line], ignore_index = True)
        self.judge_dict[tg_id] = [ False, name, LINEAR, dist, stage]

        self.judge_autentification[tg_id] = random.randint(10000, 99999)
        write_aut_info(self);
        write_judge_list(self);
        return (True, self.judge_autentification[tg_id])

    def write_aut_info(self):
        #self.filename_aut = self.filename_aut 
        with open(SECURE_DIRECTORY_NAME + self.filename_aut + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + SHEET_EXTENTION, 'W') as file:
            for line in self.judge_autentification:
                string = line + ' | ' + self.judge_autentification[line] + "\n"
                file.write(string)

    def write_judge_list(self):
        #self.filename_list = self.filename_list 
        self.judge_dict.to_excel(INFO_DIRECTORY_NAME + self.filename_list + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + SHEET_EXTENTION)

    # Можно сделать сканер директории и автоматически загружать последний по времени файл.
    def load_aut_info(self, filename: str = None): #filename без .xlsx
        if filename != None:
            self.filename_aut = filename + SHEET_EXTENTION
        else:
            if self.filename_aut == None:
                raise Exseption("Judges::load_aut_info: empty file name and empty self.filename_aut. I can't contine load")
            
        with open(SECURE_DIRECTORY_NAME + self.filename_aut, 'r') as file:
            for line in file:
                namesize = line.find(' | ')
                judgename = line[0 : namesize]
                judgepassword = line[namesize + 3 : ]
                self.judge_autentification[judgename] = (judgepassword, False, 0, 0) # tg_id : (пароль, вошёл ли в учётку,число неуспешных попыток, время последней попытки)
    # Можно сделать сканер директории и автоматически загружать последний по времени файл.
    def load_judge_list(self, filename: str):
        if filename != None:
            self.filename_list = filename
        else:
            if self.filename_list == None:
                raise Exseption("Judges::load_judge_list: empty file name and empty self.filename_list. I can't contine load")
        
        self.judge_dict = pd.read_excel(INFO_DIRECTORY_NAME + self.filename_list + SHEET_EXTENTION)
        self.judge_dict.set_index('Tg_id')

        if not set(list_of_params).issubset(self.judge_dict.columns):
            self.judge_dict = pd.DataFrame(columns = list_of_params) #Дистанции - список, этамы - словарь = {дистанция:этап}
            self.judge_dict.set_index('Tg_id')
            raise Exsepton("Judges::load_judge_list: Wrong data in filename=" + filename + ". There is no Judges::list_of_params.")

    def try_to_autentificate_judge(judge_name, judge_password: str) -> bool:
        if judge_name in self.judge_autentification.keys():
            if self.judge_autentification[judge_name] == judge_password:
                user_info = self.judge_autentification[judge_name]
                self.judge_autentification[judge_name] = (user_info[0], True, user_info[2], time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) )
                return True
            else:
                user_info = self.judge_autentification[judge_name]
                self.judge_autentification[judge_name] = (user_info[0], user_info[1], user_info[2] + 1, time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) )
                return False
        else:
            return False

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
        self.user_dict.to_excel(INFO_DIRECTORY_NAME + self.filename + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + SHEET_EXTENTION)

    def load_users(self, filename: str = None):
         if filename != None:
            self.filename = filename
         else:
            if self.filename == None:
                raise Exseption("Users::load_users: empty file name and empty self.filename. I can't contine load")
        
         self.user_dict = pd.read_excel(INFO_DIRECTORY_NAME + self.filename + SHEET_EXTENTION)
         self.user_dict.set_index('Tg_id')
         if not set(list_of_params).issubset(self.user_dict.columns):
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
        self.team_dict.to_excel(INFO_DIRECTORY_NAME + self.filename + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + SHEET_EXTENTION)

    def load_users(self, filename: str = None):
         if filename != None:
            self.filename = filename
         else:
            if self.filename == None:
                raise Exseption("Users::load_users: empty file name and empty self.filename. I can't contine load")
        
         self.team_dict = pd.read_excel(INFO_DIRECTORY_NAME + self.filename + SHEET_EXTENTION)
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
    cur_time = time.localtime(time.time())
    name = str()
    if hasattr(tt, 'name'):
        name= 'sheets\\' + type(tt).__name__ + tt.name + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + ".xlsx"
    else:
        name= 'sheets\\' + type(tt).__name__ + time.strftime("-%m.%d.%Y,%H-%M-%S", cur_time) + ".xlsx"
    df = tt.to_dafaframe()
    df.to_excel(excel_writer = "sheets\ " + type(tt) + time.ctime(time.time()) + ".xlsx")
