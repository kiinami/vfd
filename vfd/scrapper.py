import os
import sqlite3
import sys
import time
from datetime import datetime

import polars as pl
import schedule
import typer
from dateparser import parse as dateparse
from dotenv import load_dotenv
from fast_flights import FlightData, Passengers, Result, get_flights
from loguru import logger
from rich import print
from sqlalchemy.exc import OperationalError
from typing_extensions import Annotated


def get_data(start_dates: str, end_dates: str, departure_airports: str, arrival_airports: str, run_once: bool, database: str):
    logger.debug("Getting flight data")
    start_dates = start_dates.split(",")
    end_dates = end_dates.split(",")
    departure_airports = departure_airports.split(",")
    arrival_airports = arrival_airports.split(",")

    flight_plans = []
    for sdate in start_dates:
        for darp in departure_airports:
            for aarp in arrival_airports:
                flight_plans.append((sdate, darp, aarp, "outbound"))

    for edate in end_dates:
        for darp in departure_airports:
            for aarp in arrival_airports:
                flight_plans.append((edate, aarp, darp, "inbound"))


    df = pl.DataFrame(
        schema={
            "scrapped": pl.Datetime,
            "type": pl.Utf8,
            "departure_airport": pl.Utf8,
            "arrival_airport": pl.Utf8,
            "departure": pl.Datetime,
            "arrival": pl.Datetime,
            "arrival_time_ahead": pl.Utf8,
            "price": pl.Utf8,
        }
    )

    for date, darp, aarp, typ in flight_plans:
        result: Result = get_flights(
            flight_data=[
                FlightData(date=date, from_airport=darp, to_airport=aarp)
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            fetch_mode="fallback",
        )
        for flight_possibility in result.flights:
            if flight_possibility.is_best and flight_possibility.price != "Price unavailable":
                df = pl.concat(
                    [df,
                    pl.DataFrame(
                        {
                            "scrapped": [datetime.now()],
                            "type": [typ],
                            "departure_airport": [darp],
                            "arrival_airport": [aarp],
                            "departure": [dateparse(flight_possibility.departure)],
                            "arrival": [dateparse(flight_possibility.arrival)],
                            "arrival_time_ahead": [flight_possibility.arrival_time_ahead],
                            "price": [flight_possibility.price],
                        }
                    )]
                )
                logger.debug(f"Flight data found: {darp} -> {aarp} ({typ}), {flight_possibility.departure} -> {flight_possibility.arrival}, {flight_possibility.price}")

    logger.info(f"Flight data scrapped, {len(df)} data points found")

    if run_once:
        print(df)
    else:
        try:
            df.write_database(
                "flights",
                database,
                if_table_exists="append"
            )
            logger.debug(f"{len(df)} data points written to database {database}")
        except OperationalError:
            logger.error(f'Error writing to database, are you sure the database "{database}" exists and is in path "{database[10:]}"?')

def get_data_scheduled(interval, start_dates, end_dates, departure_airports, arrival_airports, run_once, database):
    logger.info(f"Running scrapper every {interval} minutes, first run in {interval} minutes")
    schedule.every(interval).minutes.do(get_data, start_dates, end_dates, departure_airports, arrival_airports, run_once, database)
    while True:
        schedule.run_pending()
        time.sleep(1)

def entrypoint(
        start_dates: Annotated[str, typer.Option(..., help="Comma separated list of start dates (in YYYY-MM-DD format)", envvar="VFD_SCRAPPER_START_DATES"),],
        end_dates: Annotated[str, typer.Option(..., help="Comma separated list of end dates (in YYYY-MM-DD format)", envvar="VFD_SCRAPPER_END_DATES"),],
        departure_airports: Annotated[str, typer.Option(..., help="Comma separated list of departure airports (in three-letter code format)", envvar="VFD_SCRAPPER_DEPARTURE_AIRPORTS"),],
        arrival_airports: Annotated[str, typer.Option(..., help="Comma separated list of arrival airports (in three-letter code format)", envvar="VFD_SCRAPPER_ARRIVAL_AIRPORTS"),],
        interval: Annotated[int, typer.Option("--interval", "-i", help="Interval in minutes to run the scrapper", envvar="VFD_SCRAPPER_INTERVAL")] = 60,
        database: Annotated[str, typer.Option("--database", "-d", help="Database to store the scrapped data", envvar="VFD_SCRAPPER_DATABASE")] = "sqlite:///data/flights.sqlite",
        run_once: Annotated[bool, typer.Option("--run-once", "-r", help="Run the scrapper once, print the data and exit")] = False,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging", envvar="VFD_SCRAPPER_VERBOSE")] = False,
):
    logger.remove()
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")

    if run_once:
        logger.debug("Running scrapper once")
        get_data(start_dates, end_dates, departure_airports, arrival_airports, run_once, database)
    else:
        get_data_scheduled(interval, start_dates, end_dates, departure_airports, arrival_airports, run_once, database)

def main():
    load_dotenv()
    typer.run(entrypoint)

if __name__ == "__main__":
    main()
