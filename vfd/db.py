import os
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger
from peewee import *

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
        return Flight.get(Flight.type == typ, Flight.scrapped == scrapped)
    except DoesNotExist:
        return None


def save_new_best_flight(best_flight: Flight, old_best_flight: Flight | None):
    if old_best_flight:
        old_best_flight.delete_instance()
    best_flight.save()
