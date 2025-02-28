import os

import polars as pl
import streamlit as st
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from streamlit.web import cli

from vfd.db import get_best_rn, Flight, get_best_ever, get_best_last_24h, get_all_flights_in_polars
from vfd.utils import now_to_the_hour as now


def render_flight(flight: Flight):
    if flight.scrapped == now().replace(tzinfo=None):
        st.success("Most likely still available!")
    elif flight.scrapped > now().replace(tzinfo=None) - relativedelta(hours=24):
        st.warning("Might still be available")
    else:
        st.error("Most likely not available anymore")
    st.title(f'{flight.departure_airport} -> {flight.arrival_airport} for ${flight.price}')
    st.write(f'Departs **{flight.departure.date()}** at **{flight.departure.strftime("%H:%M")}**')
    st.write(
        f'Arrives **{flight.arrival.date()}** at **{flight.arrival.strftime("%H:%M")}** ({flight.arrival_time_ahead})')
    st.write(f'Operated by **{flight.name}**')
    st.caption(f'Scrapped {flight.scrapped.strftime("%Y-%m-%d %H:%M")}')


def sidebar():
    with st.sidebar:
        st.title('Best flights')

        st.header(':airplane_departure: Outbound')

        best_outbound_rn = get_best_rn("outbound", now())
        if best_outbound_rn:
            with st.popover(f"Right now for ${best_outbound_rn.price}"):
                render_flight(best_outbound_rn)
        else:
            with st.popover(f"Right now unknown"):
                st.write("We don't have any data for the best outbound flight right now.")

        best_outbound_last_24h = get_best_last_24h("outbound")
        if best_outbound_last_24h:
            with st.popover(f"In the last 24 hours for ${best_outbound_last_24h.price}"):
                render_flight(best_outbound_last_24h)
        else:
            with st.popover(f"In the last 24 hours unknown"):
                st.write("We don't have any outbound flight data for the last 24 hours yet!")

        best_outbound_ever = get_best_ever("outbound")
        if best_outbound_ever:
            with st.popover(f"Best ever for ${best_outbound_ever.price}"):
                render_flight(best_outbound_ever)
        else:
            with st.popover(f"Best ever unknown"):
                st.write("We don't have any data for the best outbound flight ever.")

        st.header(':airplane_arriving: Inbound')

        best_inbound_rn = get_best_rn("inbound", now())
        if best_inbound_rn:
            with st.popover(f"Right now for ${best_inbound_rn.price}"):
                render_flight(best_inbound_rn)
        else:
            with st.popover(f"Right now unknown"):
                st.write("We don't have any data for the best inbound flight right now.")

        best_inbound_last_24h = get_best_last_24h("inbound")
        if best_inbound_last_24h:
            with st.popover(f"In the last 24 hours for ${best_inbound_last_24h.price}"):
                render_flight(best_inbound_last_24h)
        else:
            with st.popover(f"In the last 24 hours unknown"):
                st.write("We don't have any inbound flight data for the last 24 hours yet!")

        best_inbound_ever = get_best_ever("inbound")
        if best_inbound_ever:
            with st.popover(f"Best ever for ${best_inbound_ever.price}"):
                render_flight(best_inbound_ever)
        else:
            with st.popover(f"Best ever unknown"):
                st.write("We don't have any data for the best inbound flight ever.")


def content():
    st.title(':airplane: :eye: Verifiable Flight Data')

    data = get_all_flights_in_polars()
    st.header('Price history')
    # create a dataframe that for each "scrapped" value has the outbound price and the inbound price
    grouped = data.group_by("scrapped").agg(
        outbound=pl.col("price").filter(pl.col("type") == "outbound").min(),
        inbound=pl.col("price").filter(pl.col("type") == "inbound").min(),
    )
    st.line_chart(
        grouped,
        x="scrapped",
        y=["outbound", "inbound"],
        color=["#00ff00", "#0000ff"],
        x_label="Scrapped time",
        y_label="Price",
    )


def main():
    st.set_page_config(page_title=":airplane: :eye: Verifiable Flight Data", page_icon="✈️", layout="wide")
    sidebar()
    content()


def entrypoint():
    load_dotenv()
    cli.main_run([
        __file__,
        "--server.port=" + os.getenv("VFD_DASHBOARD_PORT", "4242"),
        "--server.address=" + os.getenv("VFD_DASHBOARD_HOST", "0.0.0.0"),
        "--client.toolbarMode=viewer",
        "--server.headless=true",
        "--theme.font=monospace",
        "--theme.base=dark"
    ])

if __name__ == "__main__":
    main()
