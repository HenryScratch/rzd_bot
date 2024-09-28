import motor.motor_asyncio
from bson import ObjectId

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


# import asyncio
# import json
# import pprint

# asyncio.run(fetch_city("кr"))
