import motor.motor_asyncio
from bson import ObjectId
from loguru import logger

from helpers import convert_date

# from parsing import parsing_route


client = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
db = client.telegram


async def add_user(user):
    if str(user) not in await db.list_collection_names():
        await db.create_collection(f"{user}")


async def add_routes_db(user: str, route: dict):
    src = route["src"].split("_")[1]
    dst = route["dst"].split("_")[1]
    route["url"] = (
        f"https://ticket.rzd.ru/searchresults/v/1/{src}/{dst}/{convert_date(route['date'])}"
    )
    # route['routes'] = await parsing_route(route['url'])
    logger.info("Route added to db f{route}")
    await db[f"{user}"].insert_one(route)


async def get_routes(user):
    return await db[f"{user}"].find({}).to_list(length=None)


async def delete_route_db(user, id):
    return await db[f"{user}"].delete_one({"_id": ObjectId(id)})


async def parsing_route_db(user, id):
    doc = await db[f"{user}"].find_one({"_id": ObjectId(id)})
    # r= await parsing_route(doc['url'])
    # return await parsing_route(doc['url'])


async def get_routes_db(user, id):
    # doc=await db[f"{user}"].find_one({'_id': ObjectId(id)}, )
    # r= await parsing_route(doc['url'])

    return await db[f"{user}"].find_one({"_id": ObjectId(id)}, {})


async def get_seats_variants(found_keys: list) -> list[str]:
    variants1 = [
        "Базовый",
        "Эконом",
        "Эконом+",
        "Бизнес класс",
        "Базовый (для инвалидов)",
        "Вагон-бистро",
        "Первый класс",
        "Купе-переговорная",
        "Эконом (для инвалидов)",
        "Семейный",
    ]
    variants2 = [
        "Плацкартный",
        "Купе",
        "СВ",
        "Перевозка животных без сопровождающего",
    ]

    if any(k in variants1 for k in found_keys):
        return variants1
    elif any(k in variants2 for k in found_keys):
        return variants2
    else:
        return found_keys


# import asyncio
# import json
# import pprint

# asyncio.run(fetch_city("кr"))
