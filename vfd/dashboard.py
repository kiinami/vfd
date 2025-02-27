import datetime

import polars as pl
import streamlit as st


def load_data():
    df = pl.read_database_uri(
        "SELECT * FROM flights",
        "sqlite://data/flights.sqlite",
    )

    return df


def best_combination(df: pl.DataFrame):
    outbound_lowest = (df.filter(pl.col("type") == "outbound")
                       .filter(pl.col("scrapped") >= datetime.datetime.now() - datetime.timedelta(days=1))
                       .sort("price")
                       .head(1)
                       .row(0, named=True))
    inbound_lowest = (df.filter(pl.col("type") == "inbound")
                      .filter(pl.col("scrapped") >= datetime.datetime.now() - datetime.timedelta(days=1))
                      .sort("price")
                      .head(1)
                      .row(0, named=True))

    return outbound_lowest, inbound_lowest


def possible_trips(df: pl.DataFrame):
    trips = df.select([
        "departure_airport",
        "arrival_airport",
        "type",
    ]).unique()

    return trips


def filter_by_trip(df: pl.DataFrame, trip: str):
    dep_airport, arr_airport = [el.strip() for el in trip.split("(")[0].split("->")]

    filtered = df.filter(
        (pl.col("departure_airport") == dep_airport) & (pl.col("arrival_airport") == arr_airport)
    ).select(
        pl.col("scrapped"),
        pl.col("price").map_elements(lambda s: float(s[1:]), return_dtype=pl.Float64),
    )
    print(filtered)

    return filtered


if __name__ == "__main__":
    st.set_page_config(page_title="Verifiable Flight Data", page_icon="✈️", layout="wide")

    df = load_data()
    best_outbound, best_inbound = best_combination(df)

    st.sidebar.title('Best in the last 24 hours')
    st.sidebar.write('## Outbound')
    st.sidebar.write(f'**{best_outbound["departure_airport"]}** -> **{best_outbound["arrival_airport"]}**')
    st.sidebar.write(
        f'Departs **{best_outbound["departure"].date()}** at **{best_outbound["departure"].strftime("%H:%M")}**')
    st.sidebar.write(
        f'Arrives **{best_outbound["arrival"].date()}** at **{best_outbound["arrival"].strftime("%H:%M")}**')
    st.sidebar.write(f'### {best_outbound["price"]}')
    st.sidebar.caption(f'Scrapped {best_outbound["scrapped"].strftime("%Y-%m-%d %H:%M")}')
    st.sidebar.divider()
    st.sidebar.write('## Inbound')
    st.sidebar.write(f'**{best_inbound["departure_airport"]}** -> **{best_inbound["arrival_airport"]}**')
    st.sidebar.write(
        f'Departs **{best_inbound["departure"].date()}** at **{best_inbound["departure"].strftime("%H:%M")}**')
    st.sidebar.write(f'Arrives **{best_inbound["arrival"].date()}** at **{best_inbound["arrival"].strftime("%H:%M")}**')
    st.sidebar.write(f'### {best_inbound["price"]}')
    st.sidebar.caption(f'Scrapped {best_inbound["scrapped"].strftime("%Y-%m-%d %H:%M")}')
    st.sidebar.divider()
    st.sidebar.write(f'Total price')
    st.sidebar.write(f'## ${int(best_outbound["price"][1:]) + int(best_inbound["price"][1:])}')

    st.title('Verifiable Flight Data')
    pos_trips = possible_trips(df)
    selected_trip = st.selectbox('Select trip',
                                 [f'{trip["departure_airport"]} -> {trip["arrival_airport"]} ({trip["type"]})' for trip
                                  in pos_trips.to_dicts()])

    st.scatter_chart(filter_by_trip(df, selected_trip), x="scrapped", y="price")
