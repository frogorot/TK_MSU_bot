import time
#import toml
import pandas as pd

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

class Judge:
    MAJOR, LINEAR = range(2)
        
    def __init__(self, tg_id):
        self.tg_id = tg_id # realy is a chat_id
        self.name = None # Фио
        self.status = LINEAR
        self.diastances = [] 
        self.stage = [] # Этапы дистанций
judge_dict = {}

class User:
    def __init__(self, tg_id):
        self.tg_id = tg_id # realy is a chat_id
        self.name = None # Фио
        self.age = None 
        self.sex = None
        self.university = None
        self.facility = None
        self.diastances = []
user_dict = {}

class Team:
    def __init__(self, major_id):
        self.tg_id_major = major_id #tg_id регистрирующего команду
        self.name = None
        self.distance = None
        self.slot_num = None
        self.member_id = []
        self.member_id.append(major_id)
    def __init__(self, user: User, distance): # команда на личную дистанцию
        self.tg_id_major = user.tg_id 
        self.name = user.name
        self.distance = distance
        self.slot_num = None
        self.member_id = []
        self.member_id.append(user.tg_id)
team_dict = {}

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
