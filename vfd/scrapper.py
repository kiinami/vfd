import os
from fast_flights import FlightData, Passengers, Result, get_flights
from dotenv import load_dotenv
import polars as pl
from datetime import datetime
from rich.progress import track
from dateparser import parse as dateparse

def get_data():
    load_dotenv()
    start_dates = os.environ.get("START_DATES").split(",")
    end_dates = os.environ.get("END_DATES").split(",")
    departure_airports = os.environ.get("DEPARTURE_AIRPORTS").split(",")
    arrival_airports = os.environ.get("ARRIVAL_AIRPORTS").split(",")

    flight_plans = []
    for sdate in start_dates:
        for darp in departure_airports:
            for aarp in arrival_airports:
                flight_plans.append((sdate, darp, aarp, "outbound"))

    for edate in end_dates:
        for darp in departure_airports:
            for aarp in arrival_airports:
                flight_plans.append((edate, aarp, darp, "inbound"))

    try:
        df = pl.read_database(
            query="SELECT * FROM flights",
            connection="sqlite:///flights.sqlite",
        )
    except:
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

    for date, darp, aarp, typ in track(flight_plans, description="Fetching flights..."):
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

    df.write_database(
        "flights",
        "sqlite:///flights.sqlite",
        if_table_exists="append"
    )

if __name__ == '__main__':
    get_data()
