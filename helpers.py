
import re
from datetime import datetime

date_pattern = re.compile(r"^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(\d{4})$")
cleaner_pattern = re.compile(r"[\n\xa0\{\}]")
seat_pattern = re.compile(r"Место (\d+)")


def validate_date(date):
    if re.match(date_pattern, date):
        return True
    else:
        return False

def convert_date(date):
    date_obj = datetime.strptime(date, "%d.%m.%Y")
    return date_obj.strftime("%Y-%m-%d")

def cleaner(src_string):
    return re.sub(cleaner_pattern, '', src_string.strip())

def route_print(route):
    return f"{route['station_from']} - {route['station_to']}\nНомер поезда: {route['number_route']}\n{route['time_from']} - {route['time_to']}\n{'\n'.join(( f"{k} - {v}" for k, v in route['seats'].items()))}"

def get_number_seat(text: str): 
    return re.findall(seat_pattern, text)

def find_free_seats_coupes(free_seats: list):
    total_seats=36
    seats_per_coupe = 4
    free_seats_set = set(free_seats)
    
    # Списки для купе с 4, 3 и 2 свободными местами
    fully_free_coupes = []
    three_free_coupes = []
    two_free_coupes = []
    one_free_coupes = []

    # Проверяем каждое купе
    for coupe_num in range(total_seats // seats_per_coupe):
        # Номера мест в текущем купе
        start_seat = coupe_num * seats_per_coupe + 1
        coupe_seats = {start_seat + i for i in range(seats_per_coupe)}
        
        # Находим пересечение свободных мест с местами в купе
        free_in_coupe = coupe_seats.intersection(free_seats_set)
        free_count = len(free_in_coupe)
        
        # Определяем тип купе по количеству свободных мест
        if free_count == 4:
            fully_free_coupes.append(coupe_num + 1)
        elif free_count == 3:
            three_free_coupes.append(coupe_num + 1)
        elif free_count == 2:
            two_free_coupes.append(coupe_num + 1)
        elif free_count == 1:
            one_free_coupes.append(coupe_num + 1)
    
    # Возвращаем списки купе по количеству свободных мест
    return {'4': len(fully_free_coupes), '3': len(three_free_coupes), '2': len(two_free_coupes), '1': len(one_free_coupes)}

def find_free_seats_sv(free_seats: list):
    total_seats=96
    seats_per_coupe = 2
    free_seats_set = set(free_seats)
    
    # Списки для купе с 2 свободными местами
    two_free_coupes = []
    one_free_coupes = []


    # Проверяем каждое купе
    for coupe_num in range(total_seats // seats_per_coupe):
        # Номера мест в текущем купе
        start_seat = coupe_num * seats_per_coupe + 1
        coupe_seats = {start_seat + i for i in range(seats_per_coupe)}
        
        # Находим пересечение свободных мест с местами в купе
        free_in_coupe = coupe_seats.intersection(free_seats_set)
        free_count = len(free_in_coupe)
        
        # Определяем тип купе по количеству свободных мест
        if free_count == 2:
            two_free_coupes.append(coupe_num + 1)
        elif free_count == 1:
            one_free_coupes.append(coupe_num + 1)
    
    # Возвращаем списки купе по количеству свободных мест
    return {'2': len(two_free_coupes), '1': len(one_free_coupes)}

