import asyncio
import pprint
from datetime import datetime

import motor.motor_asyncio
from bson import ObjectId
from loguru import logger

# from bson import ObjectId
from helpers import convert_date
from parsing import get_descriptions_routes, get_free_seats, get_sv_cupe, get_driver

client = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
db = client.telegram
db_queue = client.queue


def suitable_compartments(free_seats, num_seats):
    if not isinstance(free_seats, dict):
        if isinstance(free_seats, list):
            free_seats = max(map(len, free_seats))
        return free_seats if free_seats >= int(num_seats) else 0
    return sum((num_seats for k,  v in free_seats.items() if int(k) >= int(num_seats)), 0)


async def update_data():
    collections = await db.list_collection_names()
    logger.info(f"Collections: {collections}")
    al_data = []
    for collection_name in collections:
        collection = db[collection_name]

        directions = await collection.find().to_list(length=None)
        logger.info(f"directions: {directions}")

        # pprint.pprint(directions)
        for direction in directions:
            routes = await get_descriptions_routes(direction["url"])
            if not routes:
                continue
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
            # pprint.pprint(found_dict["number_route"])
            try:
                for type in direction["type_seats"]:
                    logger.info(f"Seat Type to parse: {type}")
                    type_new_data = await get_free_seats(
                        number_route=direction["number_route"],
                        url=direction["url"],
                        type_seat=type
                    )
                    if type_new_data:
                        logger.info(f"New parsed type_seats data: {type_new_data}")
                        found_dict["seats"][type] = type_new_data
                    else:
                        found_dict["seats"][type] = 0

            except Exception as e:
                logger.error(f"Problem parsing type_seats data {e}")

            sv_cupe = await get_sv_cupe(direction["number_route"], direction["url"])
            found_dict["seats"]["Купе"] = sv_cupe["Купе"]
            found_dict["seats"]["СВ"] = sv_cupe["СВ"]
            logger.info(f"AAAAJSJDJDSJSDJJSD: {found_dict}")

            result = await collection.update_one(
                {"_id": ObjectId(direction["_id"])},
                {"$set": {"seats": found_dict["seats"]}},
            )
            found_new = {}
            for type in ['СВ', 'Купе']:#direction["type_seats"]:
                logger.warning(found_dict["seats"])
                try:
                    if new_seats := suitable_compartments(found_dict["seats"][type], direction['num_seats']) - suitable_compartments(direction["seats"][type], direction['num_seats']):
                        if new_seats > 0:
                            found_new[type] = new_seats
                            logger.info(f"New suitable compartments: {found_new}")
                except KeyError:
                    pass


            # if result.modified_count > 0:
            if found_new:

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
                await asyncio.sleep(30)
            except Exception as e:
                logger.exception(e)
            finally:
                await asyncio.sleep(10)
    except Exception as e:
        logger.exception(e)



if __name__ == "__main__":

    asyncio.run(main())
