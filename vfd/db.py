import os
import sys
from datetime import datetime

import polars as pl
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from loguru import logger
from peewee import *

from vfd.utils import now_to_the_hour as now, logger_format

logger.remove()
logger.add(sys.stderr, level="INFO", format=logger_format)

load_dotenv()
db = SqliteDatabase(os.getenv("VFD_DATABASE"))


class Flight(Model):
    scrapped = DateTimeField()
    type = CharField()
    name = CharField()
    departure_airport = CharField()
    arrival_airport = CharField()
    departure = DateTimeField()
    arrival = DateTimeField()
    arrival_time_ahead = CharField()
    price = IntegerField()

    class Meta:
        database = db
        indexes = (
            (("scrapped", "type"), True),
        )


def init_db():
    db.connect()
    db.create_tables([Flight])
    db.close()
    logger.debug("Database initialized")


def get_best_rn(typ: str, scrapped: datetime):
    try:
        return Flight.get((Flight.type == typ) & (Flight.scrapped == scrapped))
    except DoesNotExist:
        return None


def get_best_last_24h(typ: str):
    try:
        return Flight.select().where(
            (Flight.type == typ) & (Flight.scrapped > now() - relativedelta(hours=24))).order_by(
            Flight.price).first()
    except DoesNotExist:
        return None


def get_best_ever(typ: str) -> Flight | None:
    try:
        return Flight.select().where(Flight.type == typ).order_by(Flight.price).first()
    except DoesNotExist:
        return None

def save_new_best_flight(best_flight: Flight, old_best_flight: Flight | None):
    if old_best_flight:
        old_best_flight.delete_instance()
    best_flight.save()


def get_all_flights_in_polars():
    data_dicts = list(Flight.select().dicts())
    return pl.DataFrame(data_dicts)
