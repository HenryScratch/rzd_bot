import json

import aiohttp
import motor.motor_asyncio

# from urllib.parse import quote
import requests

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongo:27017")
db = client.telegram
collection = db.users


async def check_user(query):
    if await collection.find_one({"user": str(query)}):
        return True
    else:
        await collection.insert_one({"user": str(query)})
        return False


# async def fetch_city(query):
#     url = f"https://ticket.rzd.ru/api/v1/suggests?GroupResults=true&RailwaySortPriority=true&Query={quote(query)}&Language=ru&TransportType=rail"

#     response_json =  requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0'}).json()
#     raw_cities = response_json['city']
#     cities = {raw_city['name']: raw_city['nodeId'] for raw_city in raw_cities}

#     return cities


# async def get_routes(id):
#     await


async def fetch_city(query):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://ticket.rzd.ru/api/v1/suggests?GroupResults=true&RailwaySortPriority=true&Query={query}&Language=ru&TransportType=rail",
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"
            },
        ) as response:
            if response.status == 200:
                html = await response.text()
                if html != "{}":
                    json_data = json.loads(html)
                    raw_cities = json_data["city"]
                    return {
                        raw_city["name"]: raw_city["nodeId"] for raw_city in raw_cities
                    }
            else:
                return None


# import asyncio
# import json
# import pprint

# asyncio.run(fetch_city("кr"))


def clear_sessions(session_id=None):
    """
    Here we query and delete orphan sessions
    docs: https://www.selenium.dev/documentation/grid/advanced_features/endpoints/
    :return: None
    """
    url = "http://127.0.0.1:4444"
    if not session_id:
        # delete all sessions
        r = requests.get("{}/status".format(url))
        data = json.loads(r.text)
        for node in data["value"]["nodes"]:
            for slot in node["slots"]:
                if slot["session"]:
                    id = slot["session"]["sessionId"]
                    r = requests.delete("{}/session/{}".format(url, id))
    else:
        # delete session from params
        r = requests.delete("{}/session/{}".format(url, session_id))


@router.message(F.text == "Отмена")
@router.message(Route_add.date_forward)
async def add_date_forward(message: Message, state: FSMContext):
    if validate_date(message.text):
        await message.answer(f"Выбрана дата: {message.text}")
        await state.update_data(date_forward=message.text)
        await state.set_state(Route_add.date_back)
        await message.answer(
            "Введите дату возвращения в формате 01.12.2024 или нажмите 'Пропустить'",
            reply_markup=skip_keyboard,
        )

        await message.answer("Обработка запроса...")
        data = await state.get_data()
        print(data)
        data["date"] = data.pop("date_forward")
        check = await check_route(data)
        if check:
            url = f"https://ticket.rzd.ru/searchresults/v/1/{data['src'].split('_')[1]}/{data['dst'].split('_')[1]}/{convert_date(data['date'])}"
            routes = await get_descriptions_routes(url)
            for route in routes:
                cupe_sv = await get_sv_cupe(route["number_route"], url)
                for key, value in cupe_sv.items():
                    route["seats"][key] = value

            # pprint.pprint(routes)

            await state.update_data(routes=routes)
            for route in routes:
                await message.answer(route_print(route))
            await message.answer(
                "Выберите маршрут для отслеживания, отправив номер поезда"
            )
            await state.set_state(Route_parsing.parsing)
        else:
            await message.answer("Нет рейсов для выбранного направления")
            await state.set_state(Route_add.input_src)
            await message.answer("Пункт отправления")
    else:
        await message.answer("Ошибка в дате, попробуйте еще раз")
        await state.set_state(Route_add.date_forward)

        # result = next((d for d in data['routes'] if d["number_route"] == message.text), None)
    # data['route'] = result
    # data['date'] = data.pop('date_forward')
    # data.pop('routes', None)
    # await add_routes_db(message.from_user.id, data)
    # await message.answer(f"Маршрут: {data['route']['number_route']} добавлен")
