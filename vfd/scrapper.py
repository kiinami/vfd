import sys
import time
from typing import Any, Generator

import typer
from apprise import Apprise
from dateparser import parse as dateparse
from dotenv import load_dotenv
from fast_flights import FlightData, Passengers, get_flights
from loguru import logger
from rich import print
from typing_extensions import Annotated

from vfd.db import Flight, init_db, get_best_rn, save_new_best_flight, get_best_ever
from vfd.utils import now_to_the_hour, logger_format


def scrape_flights(date: str, departure_airport: str, arrival_airport: str, typ: str) -> Flight | None:
    try:
        result = get_flights(
            flight_data=[
                FlightData(date=date, from_airport=departure_airport, to_airport=arrival_airport)
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            fetch_mode="local",
        )
    except AssertionError:
        logger.debug(f"No flights found from {departure_airport} to {arrival_airport} on {date}")
        return None
    best_flight = sorted(
        [flight for flight in result.flights if
         flight.price != "Price unavailable" and flight.price != 0 and flight.price != "0"],
        key=lambda x: int(x.price[1:])
    )[0]
    return Flight(
        scrapped=now_to_the_hour(),
        type=typ,
        name=best_flight.name,
        departure_airport=departure_airport,
        arrival_airport=arrival_airport,
        departure=dateparse(best_flight.departure),
        arrival=dateparse(best_flight.arrival),
        arrival_time_ahead=best_flight.arrival_time_ahead,
        price=int(best_flight.price[1:]),
    )

def combinations(start_dates: str, end_dates: str, departure_airports: str, arrival_airports: str) -> list[
    tuple[str, str, str, str]]:
    start_dates = [sd.strip() for sd in start_dates.split(",")]
    end_dates = [ed.strip() for ed in end_dates.split(",")]
    departure_airports = [da.strip() for da in departure_airports.split(",")]
    arrival_airports = [aa.strip() for aa in arrival_airports.split(",")]

    combinations = []

    for sdate in start_dates:
        for darp in departure_airports:
            for aarp in arrival_airports:
                combinations.append((sdate, darp, aarp, "outbound"))
    outbound_len = len(combinations)
    logger.debug(f"Computed {outbound_len} outbound combinations")

    for edate in end_dates:
        for darp in departure_airports:
            for aarp in arrival_airports:
                combinations.append((edate, aarp, darp, "inbound"))
    inbound_len = len(combinations) - outbound_len
    logger.debug(f"Computed {inbound_len} inbound combinations")

    return combinations


def combgen(start_dates: str, end_dates: str, departure_airports: str, arrival_airports: str) -> Generator[
    tuple[str, str, str, str], Any, Any]:
    combs = combinations(start_dates, end_dates, departure_airports, arrival_airports)
    while True:
        for comb in combs:
            yield comb


def scrapper(start_dates: str, end_dates: str, departure_airports: str, arrival_airports: str, interval: int):
    for date, darp, aarp, typ in combgen(start_dates, end_dates, departure_airports, arrival_airports):
        logger.debug(f"Getting flights from {darp} to {aarp} on {date}")

        best_flight_scrapped = scrape_flights(date, darp, aarp, typ)

        if best_flight_scrapped:
            best_flight_saved_rn = get_best_rn(typ, now_to_the_hour())
            if best_flight_saved_rn is None or best_flight_scrapped.price < best_flight_saved_rn.price:
                save_new_best_flight(best_flight_scrapped, best_flight_saved_rn)
                logger.debug(
                    f"Saved new best flight from {darp} to {aarp} on {date} for scrapped hour {best_flight_scrapped.scrapped}")

            best_flight_saved_ever = get_best_ever(typ)

            if best_flight_scrapped == best_flight_saved_ever:
                logger.log("NOTIFY",
                           f"New best {best_flight_saved_ever.type} flight found: from {darp} to {aarp} on {date} for ${best_flight_saved_ever.price}")

        if interval > 0:
            logger.debug(f"Waiting {interval} seconds before next request")
            time.sleep(interval)


def run_once_and_print(start_dates: str, end_dates: str, departure_airports: str, arrival_airports: str):
    for date, darp, aarp, typ in combgen(start_dates, end_dates, departure_airports, arrival_airports):
        logger.debug(f"Getting flights from {darp} to {aarp} on {date}")
        best_flight_rn = scrape_flights(date, darp, aarp, typ)
        print(best_flight_rn)

def entrypoint(
        start_dates: Annotated[str, typer.Option(..., help="Comma separated list of start dates (in YYYY-MM-DD format)", envvar="VFD_SCRAPPER_START_DATES"),],
        end_dates: Annotated[str, typer.Option(..., help="Comma separated list of end dates (in YYYY-MM-DD format)", envvar="VFD_SCRAPPER_END_DATES"),],
        departure_airports: Annotated[str, typer.Option(..., help="Comma separated list of departure airports (in three-letter code format)", envvar="VFD_SCRAPPER_DEPARTURE_AIRPORTS"),],
        arrival_airports: Annotated[str, typer.Option(..., help="Comma separated list of arrival airports (in three-letter code format)", envvar="VFD_SCRAPPER_ARRIVAL_AIRPORTS"),],
        interval: Annotated[
            int, typer.Option("--interval", "-i", help="Interval in seconds between each request to the API",
                              envvar="VFD_SCRAPPER_INTERVAL")] = 60,
        notification_urls: Annotated[str, typer.Option("--notification-urls", "-n",
                                                       help="Comma separated list of Apprise URLs to notify when a new best flight is found",
                                                       envvar="VFD_SCRAPPER_NOTIFICATION_URLS")] = "",
        run_once: Annotated[bool, typer.Option("--run-once", "-r", help="Run the scrapper once, print the data and exit")] = False,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging", envvar="VFD_SCRAPPER_VERBOSE")] = False,
):
    logger.remove()

    if verbose:
        logger.add(sys.stderr, level="DEBUG", format=logger_format)
    else:
        logger.add(sys.stderr, level="INFO", format=logger_format)

    logger.level("NOTIFY", no=55)
    if notification_urls:
        notification_urls = [url.strip() for url in notification_urls.split(",")]
        notifier = Apprise()
        notifier.add(notification_urls)

        logger.add(notifier.notify, level="NOTIFY", filter={"apprise": False}, format="{message}")

        logger.info(f"Notifier configured, added {len(notification_urls)} destinations")

    if run_once:
        logger.debug("Running scrapper once")
        run_once_and_print(start_dates, end_dates, departure_airports, arrival_airports)
    else:
        scrapper(start_dates, end_dates, departure_airports, arrival_airports, interval)

def main():
    load_dotenv()
    init_db()
    typer.run(entrypoint)

if __name__ == "__main__":
    main()
