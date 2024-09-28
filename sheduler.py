import asyncio
import pprint
from datetime import datetime

import motor.motor_asyncio
from bson import ObjectId

# from bson import ObjectId
from helpers import convert_date
from parsing import get_descriptions_routes, get_sv_cupe

client = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
db = client.telegram
db_queue = client.queue


async def update_data():
    collections = await db.list_collection_names()
    al_data = []
    for collection_name in collections:
        collection = db[collection_name]
        directions = await collection.find().to_list(length=None)
        # pprint.pprint(directions)
        for direction in directions:
            routes = await get_descriptions_routes(direction["url"])
            found_dict = next(
                (
                    item
                    for item in routes
                    if item.get("number_route") == direction["number_route"]
                ),
                None,
            )
            if "station_from" not in direction:
                new_fields = {
                    "station_from": found_dict["station_from"],
                    "station_to": found_dict["station_to"],
                    "time_from": found_dict["time_from"],
                    "time_to": found_dict["time_to"],
                }
                result = await collection.update_many(
                    {"_id": ObjectId(direction["_id"])}, {"$set": new_fields}
                )
            pprint.pprint(found_dict["number_route"])
            sv_cupe = await get_sv_cupe(direction["number_route"], direction["url"])
            found_dict["seats"]["Купе"] = sv_cupe["Купе"]
            found_dict["seats"]["СВ"] = sv_cupe["СВ"]
            result = await collection.update_one(
                {"_id": ObjectId(direction["_id"])},
                {"$set": {"seats": found_dict["seats"]}},
            )

            if result.modified_count > 0:
                print("modify")
                await db_queue.work.insert_one(
                    {
                        "user_id": collection_name,
                        "number_route": found_dict["number_route"],
                    }
                )


async def main():
    try:
        while True:
            try:
                print(datetime.now())
                await update_data()
                await asyncio.sleep(300)
            except Exception as e:
                print(e)
            finally:
                await asyncio.sleep(10)
    except Exception as e:
        print(e)


if __name__ == "__main__":

    asyncio.run(main())
