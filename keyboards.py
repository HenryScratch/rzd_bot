from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from transliterate import translit

from helpers import route_print

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мои маршруты")],
        [KeyboardButton(text="Добавить маршрут")],
        [KeyboardButton(text="Удалить маршрут")],
        [KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True,
)

skip_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Пропустить", callback_data="skip")]],
    resize_keyboard=True,
)


async def inline_cities(cities):
    keyboard = InlineKeyboardBuilder()
    for name, id in cities.items():
        keyboard.add(InlineKeyboardButton(text=name, callback_data=f"{name}_{id}"))
    return keyboard.adjust(1).as_markup()


async def inline_routes(routes):
    keyboard = InlineKeyboardBuilder()
    for route in routes:
        src = route["src"].split("_")[0]
        dst = route["dst"].split("_")[0]
        keyboard.add(
            InlineKeyboardButton(
                text=f"{src} - {dst} {route['date']}", callback_data=str(route["_id"])
            )
        )
    return keyboard.adjust(1).as_markup()


async def inline_routes_description(routes):
    keyboard = InlineKeyboardBuilder()
    for route in routes:
        # src = route['src'].split("_")[0]
        # dst = route['dst'].split("_")[0]
        keyboard.add(
            InlineKeyboardButton(
                text=route_print(route), callback_data=route["number_route"]
            )
        )
    return keyboard.adjust(1).as_markup()


async def inline_type_seats(seats):
    keyboard = InlineKeyboardBuilder()
    for k, seat in enumerate(seats):
        keyboard.add(
            InlineKeyboardButton(
                text=f"{seat}",
                callback_data=translit(f"{seat}", language_code="ru", reversed=True),
            )
        )
    keyboard.add(InlineKeyboardButton(text=f"Далее", callback_data="done"))
    return keyboard.adjust(1).as_markup()
