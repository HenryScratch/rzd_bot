import asyncio
import pprint

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger
from transliterate import translit

from helpers import cleaner, convert_date, route_print, validate_date
from keyboards import (
    inline_cities,
    inline_routes,
    inline_routes_description,
    inline_type_seats,
    main_keyboard,
    skip_keyboard,
)
from parsing import check_route, fetch_city, get_descriptions_routes
from utils import (
    add_routes_db,
    add_user,
    delete_route_db,
    get_routes,
    get_routes_db,
    parsing_route_db,
)

router = Router()


class Route_add(StatesGroup):
    input_src = State()
    src = State()
    input_dst = State()
    dst = State()
    date_forward = State()
    date_back = State()
    number_route_from = State()
    number_route_to = State()
    number_route_single = State()
    type_seats_selecting = State()
    type_seats_selecting_from = State()
    type_seats_done = State()
    obratno = State()


class Route_delete(StatesGroup):
    delete = State()


class Route_description(StatesGroup):
    description = State()


# class Route(StatesGroup):
#     route_forward = State()
#     route_back = State()


# Обработка комманды "/start"
@router.message(CommandStart())
async def command_start_handler(message: Message):
    logger.info("command_start_handler")

    await add_user(message.from_user.id)
    await message.answer("Выберите один из пунктов меню", reply_markup=main_keyboard)


# Обработка кнопки "Отмена"
@router.message(F.text == "Отмена")
async def cancel(message: Message, state: FSMContext):
    logger.info("cancel")

    await state.clear()
    await message.answer("Выберите один из пунктов меню", reply_markup=main_keyboard)


# Обработка кнопки "Мои маршруты"
@router.message(F.text == "Мои маршруты")
async def get_routes_state(message: Message, state: State):
    logger.info("get_routes_state")

    routes = await get_routes(message.from_user.id)
    if len(routes) > 0:
        await state.set_state(Route_description.description)
        await message.answer(
            "Выберите маршрут", reply_markup=await inline_routes(routes)
        )
    else:
        await message.answer("Нет сохраненных маршрутов")


@router.message(F.text == "Отмена")
@router.callback_query(Route_description.description)
async def pparsing_route(callback: CallbackQuery, state: FSMContext):
    logger.info("pparsing_route")

    await callback.answer("")
    # await callback.message.answer("Обработка запроса...")
    route = await get_routes_db(callback.from_user.id, callback.data)
    value = route.get("station_from", None)
    if value != None:
        mes = (
            f"{route['station_from']} - {route['station_to']}\nНомер поезда: {route['number_route']}\n{route['time_from']} - {route['time_to']}\n"
            + "\n".join(
                f"{seat_type} - {route['seats'][seat_type]}"
                for seat_type in route["type_seats"]
                if seat_type in route["seats"]
            )
        )
        await callback.message.answer(mes, reply_markup=main_keyboard)
    else:
        await callback.message.answer(
            "Данные о маршруте еще не обновлены", reply_markup=main_keyboard
        )


# Обработка кнопки "Добавить маршрут"
@router.message(F.text == "Отмена")
@router.message(F.text == "Добавить маршрут")
async def add_route(message: Message, state: FSMContext):
    logger.info("add_route")

    await state.set_state(Route_add.input_src)
    await message.answer("Пункт отправления")


@router.message(F.text == "Отмена")
@router.message(Route_add.input_src)
async def add_src(message: Message, state: FSMContext):
    logger.info("add_src")

    cities = await fetch_city(message.text)
    if cities != None:
        await message.answer(
            "Выберите из списка", reply_markup=await inline_cities(cities)
        )
        await state.set_state(Route_add.src)
    else:
        await message.answer(
            "Не существует, попробуйте еще раз",
        )
        await state.set_state(Route_add.input_src)


@router.message(F.text == "Отмена")
@router.callback_query(Route_add.src)
async def src_callback(callback: CallbackQuery, state: FSMContext):
    logger.info("src_callback")

    await callback.answer("")
    await callback.message.edit_text(f"Выбрано: {callback.data.split('_')[0]}")
    await state.update_data(src=callback.data)
    await state.set_state(Route_add.input_dst)
    await callback.message.answer("Пункт прибытия")


@router.message(F.text == "Отмена")
@router.message(Route_add.input_dst)
async def add_dst(message: Message, state: FSMContext):
    logger.info("add_dst")

    cities = await fetch_city(message.text)
    if cities != None:
        await message.answer(
            "Выберите из списка", reply_markup=await inline_cities(cities)
        )
        await state.set_state(Route_add.dst)
    else:
        await message.answer(
            "Не существует, попробуйте еще раз",
        )
        await state.set_state(Route_add.input_dst)


@router.message(F.text == "Отмена")
@router.callback_query(Route_add.dst)
async def dst_callback(callback: CallbackQuery, state: FSMContext):
    logger.info("dst_callback")

    await callback.answer("")
    await callback.message.edit_text(f"Выбрано: {callback.data.split('_')[0]}")
    await state.update_data(dst=callback.data)
    await state.set_state(Route_add.date_forward)
    await callback.message.answer("Введите дату отправления в формате 01.12.2024")


@router.message(F.text == "Отмена")
@router.message(Route_add.date_forward)
async def add_date_forward(message: Message, state: FSMContext):
    logger.info("add_date_forward")

    if validate_date(message.text):
        await message.answer(f"Выбрана дата: {message.text}")
        await state.update_data(date_forward=message.text)
        await state.set_state(Route_add.date_back)
        await message.answer(
            "Введите дату возвращения в формате 01.12.2024 или нажмите 'Пропустить'",
            reply_markup=skip_keyboard,
        )
    else:
        await message.answer("Ошибка в дате, попробуйте еще раз")
        await state.set_state(Route_add.date_forward)


@router.message(F.text == "Отмена")
@router.callback_query(Route_add.date_back)
async def date_back_callback(callback: CallbackQuery, state: FSMContext):
    logger.info("date_back_callback")

    await callback.answer("")
    await callback.message.answer("Обработка запроса...")
    data = await state.get_data()
    data["date"] = data.pop("date_forward")
    check = await check_route(data)
    if check:
        url = f"https://ticket.rzd.ru/searchresults/v/1/{data['src'].split('_')[1]}/{data['dst'].split('_')[1]}/{convert_date(data['date'])}"
        logger.info("url: {url}")

        routes = await get_descriptions_routes(url)
        await state.update_data(routes=routes)
        for route in routes:
            await callback.message.answer(route_print(route))
        await callback.message.answer(
            "Выберите маршрут для дальнейшего отслеживания, скопировав и отправив номер поезда"
        )
        await state.set_state(Route_add.number_route_single)
    else:
        await callback.message.answer("Нет рейсов для выбранного направления")
        await state.set_state(Route_add.input_src)
        await callback.message.answer("Пункт отправления")


@router.message(F.text == "Отмена")
@router.message(Route_add.number_route_single)
async def get_number_route_single(message: Message, state: FSMContext):
    logger.info("get_number_route_single")

    await state.update_data(number_route=message.text)
    data = await state.get_data()
    found_route = next(
        (item for item in data["routes"] if item.get("number_route") == message.text),
        None,
    )
    if found_route != None:
        await state.update_data(route=found_route)
        await message.answer(
            "Выберите один или несколько типов мест для отслеживания или нажмите 'Далее' для выбора всех типов сразу.",
            reply_markup=await inline_type_seats(found_route["seats"].keys()),
        )
        await state.set_state(Route_add.type_seats_selecting)
        await state.update_data(type_seats=set())
    else:
        await message.answer("Введен несуществующий маршрут, попробуйте еще раз")
        await state.set_state(Route_add.number_route_single)


@router.message(F.text == "Отмена")
@router.callback_query(Route_add.type_seats_selecting, F.data == "done")
async def type_seats_done_callback(callback: CallbackQuery, state: FSMContext):
    logger.info("type_seats_done_callback")

    logger.info(f"Seat selected: {callback.data}")

    await callback.answer("")
    data = await state.get_data()
    if len(data["type_seats"]) == 0:
        await state.update_data(type_seats=set(data["route"]["seats"].keys()))
        data = await state.get_data()
        await callback.message.edit_text(
            f"Маршрут: {data['number_route']} добавлен. Выбраны следующие категории: {', '.join(data['type_seats'])}.\nДля более детальной информации о машруте, выберите данный машрут в 'Мои маршруты'."
        )

        data["type_seats"] = list(data["type_seats"])
        data.pop("routes", None)
        data["date"] = data.pop("date_forward", None)
        await add_routes_db(callback.from_user.id, data)
        await state.clear()
    else:
        await callback.message.edit_text(
            f"Маршрут: {data['number_route']} добавлен. Выбраны следующие категории {', '.join(data['type_seats'])}.\nДля более детальной информации о машруте, выберите данный машрут в 'Мои маршруты'."
        )
        data = await state.get_data()
        data["type_seats"] = list(data["type_seats"])
        data.pop("routes", None)
        data["date"] = data.pop("date_forward", None)
        await add_routes_db(callback.from_user.id, data)
        await state.clear()


@router.message(F.text == "Отмена")
@router.callback_query(Route_add.type_seats_selecting, F.data != "done")
async def type_seats_selecting_callback(callback: CallbackQuery, state: FSMContext):
    logger.info("type_seats_selecting_callback")

    await callback.answer("")
    data = await state.get_data()
    data["type_seats"].add(
        translit(
            callback.data,
            "ru",
        )
    )
    await state.update_data(type_seats=data["type_seats"])


@router.message(F.text == "Отмена")
@router.message(Route_add.number_route_from)
async def get_number_route_from(message: Message, state: FSMContext):
    logger.info("type_seats_done_callback_from")

    await state.update_data(number_route=message.text)
    data = await state.get_data()
    logger.info(f"state.get_data: {data}")

    found_route = next(
        (item for item in data["routes"] if item.get("number_route") == message.text),
        None,
    )
    logger.info(f"found_route: {found_route}")

    if found_route != None:
        await state.update_data(route=found_route)
        await message.answer(
            "Выберите один или несколько типов мест для отслеживания или нажмите 'Далее' для выбора всех типов сразу.",
            reply_markup=await inline_type_seats(found_route["seats"].keys()),
        )
        await state.set_state(Route_add.type_seats_selecting_from)
        await state.update_data(type_seats=set())
    else:
        await message.answer("Введен несуществующий маршрут, попробуйте еще раз")
        # await state.set_state(Route_add.number_route_single)


@router.message(F.text == "Отмена")
@router.callback_query(Route_add.type_seats_selecting_from, F.data == "done")
async def type_seats_done_callback_from(callback: CallbackQuery, state: FSMContext):
    logger.info("type_seats_done_callback_from")
    await callback.answer("")
    message = callback.message
    data = await state.get_data()
    if len(data["type_seats"]) == 0:
        await state.update_data(type_seats=set(data["route"]["seats"].keys()))
        data = await state.get_data()
        await callback.message.edit_text(
            f"Маршрут: {data['number_route']} добавлен. Выбраны следующие категории: {', '.join(data['type_seats'])}.\nДля более детальной информации о машруте, выберите данный машрут в 'Мои маршруты'."
        )

        data["type_seats"] = list(data["type_seats"])
        data.pop("routes", None)
        data.pop("date_back", None)
        data.pop("obratno", None)
        data["date"] = data.pop("date_forward", None)
        await add_routes_db(callback.from_user.id, data)

        await state.set_state(Route_add.obratno)
        await add_obratno(message, state)

    else:
        data["type_seats"] = list(data["type_seats"])
        data.pop("routes", None)
        data.pop("date_back", None)
        data.pop("obratno", None)
        data["date"] = data.pop("date_forward", None)
        await add_routes_db(callback.from_user.id, data)
        await callback.message.edit_text(
            f"Маршрут: {data['number_route']} добавлен. Выбраны следующие категории: {', '.join(data['type_seats'])}.\nДля более детальной информации о машруте, выберите данный машрут в 'Мои маршруты'."
        )

        await state.set_state(Route_add.obratno)
        await add_obratno(message, state)


@router.message(F.text == "Отмена")
@router.callback_query(Route_add.type_seats_selecting_from, F.data != "done")
async def type_seats_selecting_from_callback(
    callback: CallbackQuery, state: FSMContext
):
    logger.info("type_seats_selecting_from_callback")
    await callback.answer("")
    data = await state.get_data()
    data["type_seats"].add(
        translit(
            callback.data,
            "ru",
        )
    )
    await state.update_data(type_seats=data["type_seats"])

    # await state.clear()
    # await state.update_data(number_route = message.text)
    # data = await state.get_data()
    # # !!!!!!!!!
    # data['date'] = data.pop('date_forward')
    # data.pop('date_back', None)
    # data.pop('obratno', None)
    # await add_routes_db(message.from_user.id, data)
    # await message.answer(f"Маршрут: {data['number_route']} добавлен.  Для более детальной информации о машруте, выберите данный машрут в 'Мои маршруты'.")
    # await state.set_state(Route_add.obratno)
    # await add_obratno(message, state)


@router.message(F.text == "Отмена")
@router.message(Route_add.number_route_to)
async def get_number_route(message: Message, state: FSMContext):
    # await state.update_data(number_route = message.text)
    data = await state.get_data()
    found_route = next(
        (item for item in data["routes"] if item.get("number_route") == message.text),
        None,
    )
    if found_route != None:
        await state.update_data(route=found_route)
        await message.answer(
            "Выберите один или несколько типов мест для отслеживания или нажмите 'Далее' для выбора всех типов сразу.",
            reply_markup=await inline_type_seats(found_route["seats"].keys()),
        )
        await state.set_state(Route_add.type_seats_selecting_from)
        await state.update_data(type_seats=set())
    else:
        await message.answer("Введен несуществующий маршрут, попробуйте еще раз")

    # data = await state.get_data()
    # data = data['obratno']
    # data['number_route'] = message.text
    # await add_routes_db(message.from_user.id, data)
    # await message.answer(f"Маршрут: {data['number_route']} добавлен.  Для более детальной информации о машруте, выберите данный машрут в 'Мои маршруты'.")
    # await state.clear()


@router.message(F.text == "Отмена")
@router.message(Route_add.date_back)
async def add_date_back(message: Message, state: FSMContext):
    if validate_date(message.text):
        await message.answer(f"Выбрана дата: {message.text}")
        await message.answer("Обработка запроса...")
        await state.update_data(date_back=message.text)
        data = await state.get_data()
        data1 = {}
        data1["src"], data1["dst"], data1["date"] = (
            data["dst"],
            data["src"],
            data["date_back"],
        )
        data["date"] = data.pop("date_forward")
        data.pop("date_back", None)

        check = await check_route(data)
        if check:
            url = f"https://ticket.rzd.ru/searchresults/v/1/{data['src'].split('_')[1]}/{data['dst'].split('_')[1]}/{convert_date(data['date'])}"
            routes = await get_descriptions_routes(url)
            await state.update_data(routes=routes)
            print("!!!!!!!!")
            pprint.pprint(routes)
            for route in routes:
                await message.answer(route_print(route))
            await message.answer(
                "Выберите маршрут для дальнейшего отслеживания, скопировав и отправив номер поезда"
            )
            await state.update_data(obratno=data1)
            await state.set_state(Route_add.number_route_from)
        else:
            await message.answer(
                f"Нет рейсов для выбранного направления {data['date']}"
            )
            await state.set_state(Route_add.input_src)
            await message.answer("Пункт отправления")
    else:
        await message.answer("Ошибка в дате, попробуйте еще раз")
        await state.set_state(Route_add.date_back)


@router.message(F.text == "Отмена")
@router.message(Route_add.obratno)
async def add_obratno(message: Message, state: FSMContext):
    await message.answer("Обработка запроса для обратного маршрута...")
    data = await state.get_data()
    data = data["obratno"]
    check = await check_route(data)
    if check:
        url = f"https://ticket.rzd.ru/searchresults/v/1/{data['src'].split('_')[1]}/{data['dst'].split('_')[1]}/{convert_date(data['date'])}"
        routes = await get_descriptions_routes(url)
        for route in routes:
            await message.answer(route_print(route))
        await message.answer(
            "Выберите маршрут для дальнейшего отслеживания, скопировав и отправив номер поезда"
        )
        found_route = next(
            (
                item
                for item in data["routes"]
                if item.get("number_route") == message.text
            ),
            None,
        )
        if found_route != None:
            data["route"] = found_route
            await message.answer(
                "Выберите один или несколько типов мест для отслеживания или нажмите 'Далее' для выбора всех типов сразу.",
                reply_markup=await inline_type_seats(found_route["seats"].keys()),
            )
            await state.set_state(Route_add.type_seats_selecting)
            await state.update_data(type_seats=set())
        else:
            await message.answer("Введен несуществующий маршрут, попробуйте еще раз")

        await state.set_state(Route_add.type_seats_selecting)
    else:
        await message.answer(f"Нет рейсов для выбранного направления {data['date']}")
        await state.set_state(Route_add.input_src)
        await message.answer("Пункт отправления")


# Обработка кнопки "Удалить маршрут"
@router.message(F.text == "Отмена")
@router.message(F.text == "Удалить маршрут")
async def delete_route_state(message: Message, state: FSMContext):
    routes = await get_routes(message.from_user.id)
    if len(routes) > 0:
        await state.set_state(Route_delete.delete)
        await message.answer(
            "Выберите маршрут для удаления", reply_markup=await inline_routes(routes)
        )
    else:
        await message.answer("Нет сохраненных маршрутов")


@router.message(F.text == "Отмена")
@router.callback_query(Route_delete.delete)
async def delete_route(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    await delete_route_db(callback.from_user.id, callback.data)

    routes = await get_routes(callback.from_user.id)
    if len(routes) > 0:
        await state.set_state(Route_delete.delete)
        await callback.message.edit_text(
            "Выберите маршрут для удаления", reply_markup=await inline_routes(routes)
        )
    else:
        await callback.message.edit_text("Нет сохраненных маршрутов")
        await state.clear()
