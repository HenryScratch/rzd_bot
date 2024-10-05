import asyncio
import json
import pprint
import time
from collections import Counter

import aiohttp
from loguru import logger
from selectolax.lexbor import LexborHTMLParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import (
    cleaner,
    convert_date,
    find_free_seats_coupes,
    find_free_seats_sv,
    get_number_seat,
)


def get_driver():
    logger.info("Initializing Firefox WebDriver...")
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no UI)

    # Specify the path to geckodriver if necessary (omit if in PATH)
    geckodriver_path = "./geckodriver"  # Adjust as needed

    service = FirefoxService(executable_path=geckodriver_path)

    # Initialize Firefox WebDriver with the options
    driver = webdriver.Firefox(service=service, options=options)
    logger.info("WebDriver initialized successfully.")

    return driver


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
                logger.debug(f"Fetched data for query: {query}")
                if html != "{}":
                    json_data = json.loads(html)
                    raw_cities = json_data["city"]
                    return {
                        raw_city["name"]: raw_city["nodeId"] for raw_city in raw_cities
                    }
            else:
                logger.warning(f"Failed to fetch city data: {response.status}")
                return None


async def check_route(route) -> bool:
    try:
        logger.info(f"Checking route: {route}")

        src = route["src"].split("_")[1]
        dst = route["dst"].split("_")[1]
        with get_driver() as driver:
            driver.get(
                f"https://ticket.rzd.ru/searchresults/v/1/{src}/{dst}/{convert_date(route['date'])}"
            )
            logger.info(
                f"https://ticket.rzd.ru/searchresults/v/1/{src}/{dst}/{convert_date(route['date'])}"
            )
            # driver.implicitly_wait(5)
            await asyncio.sleep(5)
            html = driver.page_source
            # driver.close()

            parser = LexborHTMLParser(html)
            cards = parser.css("div.row.card__body")
            # logger.info(f"{cards}")
            if len(cards) > 0:
                for card in cards:
                    seats = card.css_first("div.col.body__classes")
                    type_seats = seats.css("rzd-card-class")
                    if len(type_seats) > 0:
                        logger.info("Seats available for the route.")
                        return True
                logger.info("No seats available.")
                return False
            else:
                logger.error(f"No route found")
                return False
    except Exception as e:
        logger.error(f"Error checking route: {e}")
        logger.exception(e)
        # raise

    # finally:
    #     driver.quit()
    #     logger.debug("WebDriver session closed.")


async def get_free_seats(number_route: str, url: str, type_seat: str):
    logger.info(f"Fetching free seats for route {number_route} and type {type_seat}.")
    with get_driver() as driver:
        try:
            driver.get(url)
            driver.maximize_window()
            # driver.implicitly_wait(5)
            await asyncio.sleep(5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # находим все карточки с маршрутами
            routes = driver.find_elements(By.CSS_SELECTOR, "h3.card-header__title")
            for route in routes:
                if route.text == number_route:
                    route.click()
                    await asyncio.sleep(1)
                    # находим все карточки с классом обслуживания (купе, св и т.д.)
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    type_seats = driver.find_elements(
                        By.CSS_SELECTOR,
                        "h3.railway-service-class-selection-item__title",
                    )
                    for type in type_seats:
                        if type.text == type_seat:
                            type.click()
                            await asyncio.sleep(1)
                            driver.execute_script(
                                "window.scrollTo(0, document.body.scrollHeight);"
                            )
                            driver.find_element(
                                By.CSS_SELECTOR, "button.button--terminal"
                            ).click()
                            await asyncio.sleep(1)
                            driver.find_element(
                                By.CSS_SELECTOR,
                                "ui-kit-button.icon-btn.icon-btn--toggle-view-mode-btn",
                            ).click()
                            await asyncio.sleep(1)
                            # список вагонов
                            cars = driver.find_elements(
                                By.CSS_SELECTOR, "rzd-car-button"
                            )
                            cars_descriptions_list = []
                            for car in cars:
                                car.click()
                                # текст со списоком свободных мест в вагоне
                                seats = driver.find_element(
                                    By.CSS_SELECTOR, "rzd-car-seats-list-container"
                                )
                                # список свободных мест в вагоне
                                free_seats = [
                                    int(x) for x in get_number_seat(seats.text)
                                ]
                                cars_descriptions_list.append(free_seats)
                            return cars_descriptions_list
                    return None
            return None
        except Exception as err:
            # raise
            logger.exception(err)


async def get_sv_cupe(number_route: str, url: str):
    all_sv = await get_free_seats(number_route, url, "СВ")
    all_cupe = await get_free_seats(number_route, url, "Купе")

    all = {}
    if all_sv is not None:
        sv = [find_free_seats_sv(sv) for sv in all_sv]
        sv_count = Counter()
        for s in sv:
            sv_count.update(s)
        all["СВ"] = dict(sv_count)
    else:
        all["СВ"] = 0

    if all_cupe is not None:
        cupe = [find_free_seats_coupes(cupe) for cupe in all_cupe]
        cupe_count = Counter()
        for c in cupe:
            cupe_count.update(c)
        all["Купе"] = dict(cupe_count)
    else:
        all["Купе"] = 0
    return all


async def get_descriptions_routes(url: str):
    with get_driver() as driver:
        try:
            driver.get(url)
            await asyncio.sleep(5)
            # driver.implicitly_wait(5)
            # await asyncio.sleep(15)
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # находим все карточки с маршрутами
            all_data = []
            routes = driver.find_elements(By.CSS_SELECTOR, "div.row.card__body")
            logger.info(f"Routes: {routes}")

            for route in routes:
                types_seats = route.find_elements(By.CSS_SELECTOR, "rzd-card-class")
                logger.info(f"Routes: {types_seats}")

                if len(types_seats) > 0:
                    data = {}
                    data["number_route"] = cleaner(
                        route.find_element(
                            By.CSS_SELECTOR, "h3.card-header__title"
                        ).text
                    )
                    data["station_from"] = cleaner(
                        route.find_element(
                            By.CSS_SELECTOR,
                            "div.card-route__station.card-route__station--from",
                        ).text
                    )
                    data["station_to"] = cleaner(
                        route.find_element(
                            By.CSS_SELECTOR,
                            "div.card-route__station.card-route__station--to",
                        ).text
                    )
                    data["time_from"] = cleaner(
                        route.find_element(
                            By.CSS_SELECTOR,
                            "div.card-route__date-time.card-route__date-time--from",
                        ).text
                    )
                    data["time_to"] = cleaner(
                        route.find_element(
                            By.CSS_SELECTOR,
                            "div.card-route__date-time.card-route__date-time--to",
                        ).text
                    )
                    data_seats = {}
                    for type in types_seats:
                        name = cleaner(
                            type.find_element(
                                By.CSS_SELECTOR, "div.card-class__name"
                            ).text
                        )
                        data_seats[name] = cleaner(
                            type.find_element(
                                By.CSS_SELECTOR, "div.card-class__quantity"
                            ).text
                        )
                        data["seats"] = data_seats
                    all_data.append(data)
            # driver.close()
            logger.info(f"all_data: {all_data}")

            return all_data

        except Exception as err:
            logger.exception(err)


# async def main():
#     r = await get_sv_cupe(number_route, url)
#     pprint.pprint(r)


# number_route = "002Э"
# url = "https://ticket.rzd.ru/searchresults/v/1/5a323c29340c7441a0a556bb/5a13bd09340c745ca1e87e37/2024-10-01"

# asyncio.run(main())
