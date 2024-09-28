def find_free_coupes(free_seats, total_seats=36):
    seats_per_coupe = 4
    free_seats_set = set(free_seats)

    # Списки для купе с 4, 3 и 2 свободными местами
    fully_free_coupes = []
    three_free_coupes = []
    two_free_coupes = []

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

    # Возвращаем списки купе по количеству свободных мест
    return fully_free_coupes, three_free_coupes, two_free_coupes


# Пример использования
free_seats = [
    1,
    2,
    3,
    4,
    7,
    8,
    9,
    10,
    12,
    14,
    15,
    16,
    18,
    20,
    22,
    24,
    26,
    28,
    30,
    32,
    34,
    36,
]
full_free, three_free, two_free = find_free_coupes(free_seats)

print(f"Полностью свободные купе: {full_free}")
print(f"Купе с тремя свободными местами: {three_free}")
print(f"Купе с двумя свободными местами: {two_free}")
