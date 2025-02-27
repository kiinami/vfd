import datetime

import polars as pl
import streamlit as st


def load_data():
    df = pl.read_database_uri(
        "SELECT * FROM flights",
        "sqlite://data/flights.sqlite",
    )

    return df


def best_combination_last_24h(df: pl.DataFrame):
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


def best_by_hour(df: pl.DataFrame):
    # Ensure the DataFrame is sorted by the 'scrapped' timestamp
    df = df.sort("scrapped")

    # Group by 'scrapped' time in 1-hour intervals and by 'type'
    grouped = df.group_by_dynamic(
        index_column="scrapped",
        every="1h",
        group_by="type",
        closed="left",  # Define which side of the interval is closed
    ).agg(
        # Calculate the minimum price for each group
        price=pl.col("price").min(),
        # Get the row with the minimum price
        name=pl.col("name").first(),
        departure_airport=pl.col("departure_airport").first(),
        arrival_airport=pl.col("arrival_airport").first(),
        departure=pl.col("departure").first(),
        arrival=pl.col("arrival").first()
    )

    inbound_grouped = grouped.filter(pl.col("type") == "inbound").rename(
        {
            "price": "inbound_price",
            "name": "inbound_name",
            "departure_airport": "inbound_departure_airport",
            "arrival_airport": "inbound_arrival_airport",
            "departure": "inbound_departure",
            "arrival": "inbound_arrival",
        }
    )

    outbound_grouped = grouped.filter(pl.col("type") == "outbound").rename(
        {
            "price": "outbound_price",
            "name": "outbound_name",
            "departure_airport": "outbound_departure_airport",
            "arrival_airport": "outbound_arrival_airport",
            "departure": "outbound_departure",
            "arrival": "outbound_arrival",
        }
    )

    best_trips = inbound_grouped.join(
        outbound_grouped,
        on="scrapped",
        how="inner",
    ).drop("type")

    best_trips = best_trips.insert_column(
        index=1,
        column=(pl.col("inbound_price") + pl.col("outbound_price")).alias("price")
    ).drop("inbound_price", "outbound_price")

    return best_trips

if __name__ == "__main__":
    st.set_page_config(page_title="Verifiable Flight Data", page_icon="✈️", layout="wide")

    df = load_data()
    best_outbound_last_24h, best_inbound_last_24h = best_combination_last_24h(df)

    st.sidebar.title('Stats')
    with st.sidebar.expander("Best in the last 24 hours"):
        st.write('## Outbound')
        st.write(
            f'**{best_outbound_last_24h["departure_airport"]}** -> **{best_outbound_last_24h["arrival_airport"]}** ({best_outbound_last_24h["name"]})')
        st.write(
            f'Departs **{best_outbound_last_24h["departure"].date()}** at **{best_outbound_last_24h["departure"].strftime("%H:%M")}**')
        st.write(
            f'Arrives **{best_outbound_last_24h["arrival"].date()}** at **{best_outbound_last_24h["arrival"].strftime("%H:%M")}**')
        st.write(f'### ${best_outbound_last_24h["price"]}')
        st.caption(f'Scrapped {best_outbound_last_24h["scrapped"].strftime("%Y-%m-%d %H:%M")}')
        st.sidebar.divider()
        st.write('## Inbound')
        st.write(
            f'**{best_inbound_last_24h["departure_airport"]}** -> **{best_inbound_last_24h["arrival_airport"]}** ({best_inbound_last_24h["name"]})')
        st.write(
            f'Departs **{best_inbound_last_24h["departure"].date()}** at **{best_inbound_last_24h["departure"].strftime("%H:%M")}**')
        st.write(
            f'Arrives **{best_inbound_last_24h["arrival"].date()}** at **{best_inbound_last_24h["arrival"].strftime("%H:%M")}**')
        st.write(f'### ${best_inbound_last_24h["price"]}')
        st.caption(f'Scrapped {best_inbound_last_24h["scrapped"].strftime("%Y-%m-%d %H:%M")}')
        st.divider()
        st.write(f'Total price')
        st.write(f'## ${best_outbound_last_24h["price"] + best_inbound_last_24h["price"]}')

    with st.sidebar.expander("Best ever"):
        st.write("To be implemented")

    st.title('Verifiable Flight Data')
    st.line_chart(best_by_hour(df), x="scrapped", y="price")
