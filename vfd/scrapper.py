import os
import time

import schedule
from fast_flights import FlightData, Passengers, Result, get_flights
from dotenv import load_dotenv
import polars as pl
from datetime import datetime
from dateparser import parse as dateparse
from loguru import logger

def get_data():
    logger.info("Started fetch flights job")
    start_dates = os.getenv("START_DATES").split(",")
    end_dates = os.getenv("END_DATES").split(",")
    departure_airports = os.getenv("DEPARTURE_AIRPORTS").split(",")
    arrival_airports = os.getenv("ARRIVAL_AIRPORTS").split(",")

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

    if not os.path.isdir('data'):
        os.mkdir('data')
    df.write_database(
        "flights",
        "sqlite:///data/flights.sqlite",
        if_table_exists="append"
    )
    logger.info(f"Finished fetch flights job, added {len(df)} data points to the database")

def main_scheduled():
    load_dotenv()
    logger.info(f"Starting scrapper scheduled job to run every {os.getenv('SCRAPE_INTERVAL', 60)} minutes")
    schedule.every(int(os.getenv("SCRAPE_INTERVAL", 60))).minutes.do(get_data)
    while True:
        schedule.run_pending()
        time.sleep(1)
